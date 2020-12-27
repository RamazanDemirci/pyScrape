from PIL import Image
import requests
import glob

#imagelist = []
imagelist = glob.glob('img/*.jpg')

cover_url = "http://www.ataekitap.com/e-kitaplar/ortaokul/5-sinif/5_Sinif_Ben_Korkmam_Fen_Bilimleri_Soru_Bankasi/files/mobile/1.jpg?200725164621"

img_cover = Image.open(requests.get(cover_url, stream = True).raw)

for i in range(2,306):
    print(f"process in {i}/305")
    image_url = f"http://www.ataekitap.com/e-kitaplar/ortaokul/5-sinif/5_Sinif_Ben_Korkmam_Fen_Bilimleri_Soru_Bankasi/files/mobile/{i}.jpg?200725164621"
    try:
        img = Image.open(requests.get(image_url, stream = True).raw)
        imagelist.append(img)
    except:
        print(f"Page {i} not exist!")
        


img_cover.save("5_Sinif_Ben_Korkmam_Fen_Bilimleri_Soru_Bankasi.pdf", "PDF" ,resolution=100.0, save_all=True, append_images=imagelist)
