import os
from PIL import Image
import torchvision.transforms as transforms
import torchvision.transforms.functional as TF
from torchvision.transforms import ToPILImage

from tqdm import tqdm

def prepro_satellite():

    input_folder = 'data/raw/gang_nam_apt_images'
    output_folder = 'data/interim/satellites/'

    # 다양한 각도로 Random Rotation하여 실험해보기
    degrees = [0, 90, 180, 270, 360]

    base_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(
            # mean=[0.485, 0.456, 0.406],
            # std=[0.229, 0.224, 0.225]
            mean=[0.0, 0.0, 0.0],  # 평균 0
            std=[1.0, 1.0, 1.0]    # 분산 1
        )
    ])


    os.makedirs(output_folder, exist_ok=True)


    to_pil = ToPILImage()

    for degree in degrees:
        degree_folder = os.path.join(output_folder, f'rot_{degree}')
        os.makedirs(degree_folder, exist_ok=True)

        filenames = [f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        for filename in tqdm(filenames, desc=f'Rotation {degree}'):
            img_path = os.path.join(input_folder, filename)
            img = Image.open(img_path).convert('RGB')

            rotated_img = TF.rotate(img, degree, fill=(255, 255, 255))

            augmented_img = base_transform(rotated_img)
            augmented_img_pil = to_pil(augmented_img)

            save_path = os.path.join(degree_folder, filename)
            augmented_img_pil.save(save_path)