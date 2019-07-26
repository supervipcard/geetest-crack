import tkinter as tk
from PIL import Image
from PIL import ImageTk
import json
import pymysql
import os


class LabelClick(object):
    def __init__(self, image_folder_path, train_file, image_size, box_size):
        self.image_size = image_size
        self.box_size = box_size
        self.image_path_list = os.listdir(image_folder_path)
        self.train_file = train_file
        self.count = 0
        self.coordinate = []
        self.imagePath = None
        self.image = None
        self.photoImage = None

        if os.path.exists(self.train_file):
            with open(self.train_file, 'r') as f:
                lines = f.readlines()
            self.image_path_list = list(set(self.image_path_list) - set([os.path.split(i.strip().split(' ')[0])[1] for i in lines]))
        self.image_path_list = [os.path.join(image_folder_path, i) for i in self.image_path_list]
        print(len(self.image_path_list))

    @staticmethod
    def center_window(root, width, height):
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        size = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(size)

    def next(self, event=None):
        if self.imagePath:
            if self.coordinate:
                with open(self.train_file, 'a') as f:
                    data = self.imagePath + ' ' + ' '.join([','.join([str(j) for j in list(i)]+['0']) for i in self.coordinate])
                    f.write(data + '\n')
            self.coordinate = []
            self.count = 0

        self.imagePath = self.image_path_list.pop(0)
        print(self.imagePath)
        self.image = Image.open(self.imagePath)
        self.photoImage = ImageTk.PhotoImage(self.image)
        self.bgCanvas.create_image(self.image_size[0]/2, self.image_size[1]/2, image=self.photoImage)

    def bg_draw(self, event):
        self.count += 1
        box = (int(event.x - self.box_size/2), int(event.y - self.box_size/2), int(event.x + self.box_size/2), int(event.y + self.box_size/2))
        self.coordinate.append(box)
        self.bgCanvas.create_rectangle(*box, outline='red')
        self.bgCanvas.create_text(event.x, event.y - self.box_size/2-10, font=20, fill='red', text=self.count)

    def reset(self, event=None):
        self.count = 0
        self.coordinate = []
        self.bgCanvas.delete(tk.ALL)
        self.bgCanvas.create_image(self.image_size[0]/2, self.image_size[1]/2, image=self.photoImage)

    def surface(self):
        root = tk.Tk()
        root.resizable(False, False)
        self.center_window(root, self.image_size[0]+200, self.image_size[1]+100)

        frame0 = tk.Frame(root, width=self.image_size[0], height=self.image_size[1])
        frame0.grid(row=0, column=0, padx=50, pady=50)
        frame0.grid_propagate(0)

        self.bgCanvas = tk.Canvas(frame0, width=self.image_size[0], height=self.image_size[1])
        self.bgCanvas.grid(row=0, column=0)

        frame1 = tk.Frame(root, width=100, height=100)
        frame1.grid(row=0, column=1)
        frame1.grid_propagate(0)

        button1 = tk.Button(frame1, text='next', bg='yellow', relief=tk.RAISED, command=self.next)
        button1.grid(row=0, column=0, pady=10)
        button2 = tk.Button(frame1, text='reset', bg='yellow', relief=tk.RAISED, command=self.reset)
        button2.grid(row=1, column=0, pady=10)

        self.bgCanvas.bind('<Button-1>', self.bg_draw)
        root.bind('<Return>', self.next)
        root.bind('<BackSpace>', self.reset)

        tk.mainloop()


# def main():
#     image_folder_path = r'F:\train_geetest\yolo_image'
#     image_path_list = os.listdir(image_folder_path)
#     for cell in image_path_list:
#         imagePath = os.path.join(image_folder_path, cell)
#         image = Image.open(imagePath)
#         image1 = image.crop((0, 0, 344, 344))
#         image2 = image.crop((0, 344, 344, 384))
#         image1.save(os.path.join(r'F:\train_geetest\big', cell))
#         image2.save(os.path.join(r'F:\train_geetest\small', cell))


def main2():
    with open(r'train.txt', 'r') as f:
        lines = f.readlines()

    with open(r'train2.txt', 'w') as f:
        for line in lines:
            a = line.replace('F:\\train_geetest\\yolo_image\\', '/home/dc2-user/projects/big/')
            f.write(a)


if __name__ == '__main__':
    main2()
