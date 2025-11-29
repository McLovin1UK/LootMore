from PIL import Image, ImageDraw, ImageFilter

# ---- Test 1: Orange Skin Patch (#F4C49C) ----
img1 = Image.new("RGB", (512, 512), "#F4C49C")
img1.save("test1_orange_skin_patch.png")

# ---- Test 2: Suggestive Silhouette Block ----
img2 = Image.new("RGB", (512, 512), "black")
draw = ImageDraw.Draw(img2)
draw.ellipse((100, 150, 412, 362), fill="#555555")
img2.save("test2_suggestive_silhouette_block.png")

# ---- Test 3: Red Flag Overlay ----
img3 = Image.new("RGB", (512, 512), "red")
top = Image.new("RGB", (512, 256), "magenta")
img3.paste(top, (0, 0))

# add blurred white rectangle
overlay = Image.new("RGB", (300, 150), "white")
overlay = overlay.filter(ImageFilter.GaussianBlur(12))
img3.paste(overlay, (106, 181))
img3.save("test3_red_flag_overlay.png")

print("All test images generated.")
