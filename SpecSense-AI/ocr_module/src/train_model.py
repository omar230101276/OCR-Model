import os
import pandas as pd
import shutil
import subprocess
import sys
from sklearn.model_selection import train_test_split

class OCRTrainer:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.training_dir = os.path.join(data_dir, "training")
        self.trainer_repo_path = os.path.join(data_dir, "deep-text-recognition-benchmark")
        
        if not os.path.exists(self.training_dir):
            os.makedirs(self.training_dir)

    def setup_training_env(self):
        """
        Download official training repo if not exists.
        """
        if not os.path.exists(self.trainer_repo_path):
            print("Cloning training repository (deep-text-recognition-benchmark)...")
            try:
                subprocess.check_call(["git", "clone", "https://github.com/ClovaAI/deep-text-recognition-benchmark.git", self.trainer_repo_path])
                print("Clone successful.")
            except Exception as e:
                print(f"Clone failed: {e}")
                return False
        else:
            print("Training repository already exists.")
        return True

    def prepare_dataset(self, labels_file):
        """
        Prepare dataset for training.
        :param labels_file: CSV file containing (filename, text)
        """
        if not os.path.exists(labels_file):
            print(f"Labels file not found: {labels_file}")
            return

        print("Reading data...")
        df = pd.read_csv(labels_file)
        
        # Split train/validation
        train, val = train_test_split(df, test_size=0.1, random_state=42)
        
        # Create subdirectories for images
        train_img_dir = os.path.join(self.training_dir, "train_images")
        val_img_dir = os.path.join(self.training_dir, "val_images")
        os.makedirs(train_img_dir, exist_ok=True)
        os.makedirs(val_img_dir, exist_ok=True)

        print("Copying images...")
        self._copy_images(train, train_img_dir)
        self._copy_images(val, val_img_dir)

        # Create gt.txt files required by create_lmdb_dataset.py
        self._create_gt_file(train, os.path.join(self.training_dir, "gt_train.txt"))
        self._create_gt_file(val, os.path.join(self.training_dir, "gt_val.txt"))

        print("\n--- Training Instructions ---")
        print("1. Install training libraries: pip install fire lmdb nltk natsort")
        print("2. Create LMDB files:")
        print(f"   python \"{self.trainer_repo_path}/create_lmdb_dataset.py\" --inputPath \"{self.training_dir}/train_images\" --gtFile \"{self.training_dir}/gt_train.txt\" --outputPath \"{self.training_dir}/data_lmdb_train\"")
        print(f"   python \"{self.trainer_repo_path}/create_lmdb_dataset.py\" --inputPath \"{self.training_dir}/val_images\" --gtFile \"{self.training_dir}/gt_val.txt\" --outputPath \"{self.training_dir}/data_lmdb_val\"")
        print("3. Start Training:")
        print(f"   python \"{self.trainer_repo_path}/train.py\" --train_data \"{self.training_dir}/data_lmdb_train\" --valid_data \"{self.training_dir}/data_lmdb_val\" --select_data / --batch_ratio 1.0 --Talignment --Transformation TPS --FeatureExtraction ResNet --SequenceModeling BiLSTM --Prediction Attn")

    def _copy_images(self, df, target_dir):
        for _, row in df.iterrows():
            src = os.path.join(self.raw_dir, row['filename'])
            dst = os.path.join(target_dir, row['filename'])
            if os.path.exists(src):
                shutil.copy(src, dst)
            else:
                print(f"Warning: Image {src} not found.")

    def _create_gt_file(self, df, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                f.write(f"{row['filename']}\t{row['text']}\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", help="Path to CSV file containing (filename, text)")
    parser.add_argument("--data_dir", default="O:/OCR Model/data", help="Main data directory")
    args = parser.parse_args()

    trainer = OCRTrainer(args.data_dir)
    trainer.setup_training_env()
    
    if args.labels:
        trainer.prepare_dataset(args.labels)
    else:
        print("Use --labels to specify data file to start preparation.")
