"""利用opencv读取并显示一个目录下的全部图片"""
import os
import cv2

def readpics(directory_name):
    for filename in os.listdir(r"./"+directory_name):

        if (filename.endswith(".jpg")):

            image = cv2.imread(directory_name + "/" + filename)
            image = cv2.resize(image, (551, 551))

            cv2.imshow("image", image)

        # 每张图片的停留时间
            k = cv2.waitKey(10)

        # 通过esc键终止程序
            if k == 27:
                break


readpics("Basketball/img")
cv2.destroyAllWindows()
