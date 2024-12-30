import os
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Configuration       
cloudinary.config( 
    cloud_name = "dsz7vteia", 
    api_key = "518958831376495", 
    api_secret = "ckljKanR8caFgGQOE0JHM7I6IZM", 
    secure=True
)

# Path to the folder containing images
folder_path = r"C:\Users\MINH\Documents\Zalo_Received_Files\CNPM\BookFlask\bookmanagerapp\app\static\Fahasa"

# Iterate through all files in the folder
for filename in os.listdir(folder_path):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        file_path = os.path.join(folder_path, filename)
        # Upload the image
        upload_result = cloudinary.uploader.upload(file_path, public_id=os.path.splitext(filename)[0])
        print(f"Uploaded {filename}: {upload_result['secure_url']}")

        # Optimize delivery by resizing and applying auto-format and auto-quality
        optimize_url, _ = cloudinary_url(os.path.splitext(filename)[0], fetch_format="auto", quality="auto")
        print(f"Optimized URL for {filename}: {optimize_url}")
        with open('image_url.txt', 'a') as f:
                    f.write(f"{filename}: {optimize_url}\n")
        # Transform the image: auto-crop to square aspect_ratio
        # auto_crop_url, _ = cloudinary_url(os.path.splitext(filename)[0], width=500, height=500, crop="auto", gravity="auto")
        # print(f"Auto-cropped URL for {filename}: {auto_crop_url}")
        