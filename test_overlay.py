import tkinter as tk

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)

# --- Position top-right ---
WIDTH, HEIGHT = 350, 80
screen_w = root.winfo_screenwidth()
x = screen_w - WIDTH - 20
y = 20
root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")

# Fully transparent window
root.attributes("-alpha", 0.0)  # invisible base window

# --- Floating text ---
text = tk.Label(
    root,
    text="Lootmore AI Online\nWaiting for screenshot...",
    fg="#0a0a0a",              # change this if you want white/grey/whatever
    bg=None,
    font=("Consolas", 16, "bold"),   # bigger, cleaner
    justify="left"
)
text.pack()

# Bring only the text back to visible
text.attributes = root.attributes  # keep reference (tk quirk)
root.attributes("-alpha", 1.0)

root.mainloop()
