import os

# هذا السطر يجعل الكود يعمل على المجلد الحالي مهما كان اسمه
folder_path = os.getcwd()

print(f"working in: {folder_path}")

for filename in os.listdir(folder_path):
    # نتأكد أنه ملف نصي وفيه علامة الشرطة ومش هو ملف السكربت نفسه
    if filename.endswith(".txt") and "-" in filename and filename != "fix.py":
        try:
            # فصل الكود الغريب عن الاسم الحقيقي
            parts = filename.split('-', 1)
            
            if len(parts) > 1:
                new_name = parts[1] # نأخذ الجزء الثاني (الاسم النظيف)
                
                old_file = os.path.join(folder_path, filename)
                new_file = os.path.join(folder_path, new_name)
                
                # تنفيذ إعادة التسمية
                os.rename(old_file, new_file)
                print(f"Fixed: {filename} -> {new_name}")
        except Exception as e:
            print(f"Error file {filename}: {e}")

print("Done! All filenames are clean.")