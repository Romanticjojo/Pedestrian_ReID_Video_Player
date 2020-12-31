import cmath
import os
import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, pyqtBoundSignal, QEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QLabel, QGridLayout
import cv2
import requests
import base64
from client import detect_person_reid, plot_one_box

BASE_DIR = os.path.dirname(__file__)
path = BASE_DIR.replace('\\'[0], '/')
selectcolor = [255, 0, 0]

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('/Users/danieltang/Downloads/Pedestrian Re-ID Software/poseVideo.ui', self)
        self.setWindowTitle('Video Player')
        # create a timer
        self.timer = QTimer()
        self.timer2 = QTimer()
        # set timer timeout callback function
        self.timer.timeout.connect(self.playVideo)
        self.timer2.timeout.connect(self.playVideo2)
        # set control_bt callback clicked  function
        #screen 1
        self.playButton.clicked.connect(self.playTimer)
        self.pauseButton.clicked.connect(self.stopTimer)
        self.video2picsButton.clicked.connect(self.video2frame)
        self.readpicsButton.clicked.connect(self.readpics)
        self.stopButton.clicked.connect(self.videostop)
        self.doubleButton.clicked.connect(self.doubleplay)
        self.browseButton.clicked.connect(self.openFile)
        self.slider.valueChanged.connect(self.skipFrame)
        self.comboBox.activated[str].connect(self.fpschange)

        #screen2
        self.playButton2.clicked.connect(self.playTimer2)
        self.pauseButton2.clicked.connect(self.stopTimer2)
        self.stopButton2.clicked.connect(self.videostop2)
        self.doubleButton2.clicked.connect(self.doubleplay2)
        self.browseButton2.clicked.connect(self.openFile2)
        self.slider2.valueChanged.connect(self.skipFrame2)
        self.comboBox2.activated[str].connect(self.fpschange2)

        self.stopread = False
        self.stopread2 = False
        self.sendButton.clicked.connect(self.Send)

        # self.ReIDButton.clicked.connect(self.ReID)

    def fpschange(self, text):
        if text=="10fps":
            self.timer.stop()
            fps = 10
            self.timer.start(1000 / fps)
        elif text=="15fps":
            self.timer.stop()
            fps = 15
            self.timer.start(1000 / fps)
        elif text=="20fps":
            self.timer.stop()
            fps = 20
            self.timer.start(1000 / fps)
        elif text=="25fps":
            self.timer.stop()
            fps = 25
            self.timer.start(1000 / fps)
        elif text=="30fps":
            self.timer.stop()
            fps = 30
            self.timer.start(1000 / fps)

    def fpschange2(self, text):
        if text=="10fps":
            self.timer2.stop()
            fps = 10
            self.timer2.start(1000 / fps)
        elif text=="15fps":
            self.timer2.stop()
            fps = 15
            self.timer2.start(1000 / fps)
        elif text=="20fps":
            self.timer2.stop()
            fps = 20
            self.timer2.start(1000 / fps)
        elif text=="25fps":
            self.timer2.stop()
            fps = 25
            self.timer2.start(1000 / fps)
        elif text=="30fps":
            self.timer2.stop()
            fps = 30
            self.timer2.start(1000 / fps)


    def space(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()

    def skipFrame(self):
        value = self.slider.value()
        self.cap.set(1, value)

    def skipFrame2(self):
        value = self.slider2.value()
        self.cap2.set(1, value)

    def playVideo(self):
        # read image in BGR format
        global box_pos_x1, box_pos_x2, box_pos_y1, box_pos_y2, pedestrian_id
        ret = False
        if not self.stopread:
            ret, image = self.cap.read()
        #
        #     image = cv2.resize(image, (551, 551))
        #     info = {'img': image, 'frame_num': int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))}
        #     url = "http://www.wujiacloud.top:6060/photo"
        #     succ, people, _ = detect_person_reid(info, url)
        #     if people:
        #         for p in people:
        #             plot_one_box(p['pos'], image, label=str(p['person_id']), color=[255, 255, 0])
        #             box_pos_x1 = int(p['pos'][0])
        #             box_pos_x2 = int(p['pos'][2])
        #             box_pos_y1 = int(p['pos'][1])
        #             box_pos_y2 = int(p['pos'][3])
        #             pedestrian_id = str(p['person_id'])

        # else:
        #     ret, image = True, self.render_frame
        if ret is True:
            progress = str(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))) + ' / ' \
                       + str(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.progresslabel.setText(progress)
            self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
            # convert image to RGB format
            # resize image
            image = cv2.resize(image, (551, 551))
            info = {'img': image, 'frame_num': int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))}
            url = "http://www.wujiacloud.top:6060/mot"
            succ, people, _ = detect_person_reid(info, url)
            if people:
                for p in people:
                    plot_one_box(p['pos'], image, label=str(p['person_id']), color=[255, 255, 0])
                    box_pos_x1 = int(p['pos'][0])
                    box_pos_x2 = int(p['pos'][2])
                    box_pos_y1 = int(p['pos'][1])
                    box_pos_y2 = int(p['pos'][3])
                    pedestrian_id = str(p['person_id'])
            self.current_frame_p = people
            # get image infos
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.render_frame = image
            height, width, channel = image.shape
            step = channel * width
            # create QImage from image
            qImg = QImage(self.render_frame.data, width, height, step, QImage.Format_RGB888)
            # show image in img_label
            self.display.setPixmap(QPixmap.fromImage(qImg))
        else:
            # progress = str(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))) + ' / ' \
            #            + str(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            # self.progresslabel.setText(progress)
            # self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
            if self.stopread:
                eight, width, channel = self.render_frame.shape
                step = channel * width
                # create QImage from image
                qImg = QImage(self.render_frame.data, 551, 551, step, QImage.Format_RGB888)
                # show image in img_label
                self.display.setPixmap(QPixmap.fromImage(qImg))
            else:
                # raise ValueError()
                pass
    def playVideo2(self):
        # read image in BGR format
        global box_pos_x1, box_pos_x2, box_pos_y1, box_pos_y2, pedestrian_id
        ret = False
        if not self.stopread2:
            ret, image = self.cap2.read()
        #
        #     image = cv2.resize(image, (551, 551))
        #     info = {'img': image, 'frame_num': int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))}
        #     url = "http://www.wujiacloud.top:6060/photo"
        #     succ, people, _ = detect_person_reid(info, url)
        #     if people:
        #         for p in people:
        #             plot_one_box(p['pos'], image, label=str(p['person_id']), color=[255, 255, 0])
        #             box_pos_x1 = int(p['pos'][0])
        #             box_pos_x2 = int(p['pos'][2])
        #             box_pos_y1 = int(p['pos'][1])
        #             box_pos_y2 = int(p['pos'][3])
        #             pedestrian_id = str(p['person_id'])

        # else:
        #     ret, image = True, self.render_frame
        if ret is True:
            progress = str(int(self.cap2.get(cv2.CAP_PROP_POS_FRAMES))) + ' / ' \
                       + str(int(self.cap2.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.progresslabel2.setText(progress)
            self.slider2.setValue(int(self.cap2.get(cv2.CAP_PROP_POS_FRAMES)))
            # convert image to RGB format
            # resize image
            image = cv2.resize(image, (551, 551))
            info = {'img': image, 'frame_num': int(self.cap2.get(cv2.CAP_PROP_POS_FRAMES))}
            url = "http://www.wujiacloud.top:6060/reid"
            succ, people, _ = detect_person_reid(info, url)
            if people:
                for p in people:
                    plot_one_box(p['pos'], image, label=str(p['person_id']), color=[255, 255, 0])
                    box_pos_x1 = int(p['pos'][0])
                    box_pos_x2 = int(p['pos'][2])
                    box_pos_y1 = int(p['pos'][1])
                    box_pos_y2 = int(p['pos'][3])
                    pedestrian_id = str(p['person_id'])
            self.current_frame_p2 = people
            # get image infos
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.render_frame2 = image
            height, width, channel = image.shape
            step = channel * width
            # create QImage from image
            qImg = QImage(self.render_frame2.data, width, height, step, QImage.Format_RGB888)
            # show image in img_label
            self.display2.setPixmap(QPixmap.fromImage(qImg))
        else:
            # progress = str(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))) + ' / ' \
            #            + str(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            # self.progresslabel.setText(progress)
            # self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
            if self.stopread2:
                eight, width, channel = self.render_frame2.shape
                step = channel * width
                # create QImage from image
                qImg = QImage(self.render_frame2.data, 551, 551, step, QImage.Format_RGB888)
                # show image in img_label
                self.display2.setPixmap(QPixmap.fromImage(qImg))
            else:
                # raise ValueError()
                pass

    def detect_person_reid(info, url):
        """
            Args:
                info: dict of a frame {'img':im, 'frame_num':int}
                url: string of server
        """
        frame_num = info['frame_num']
        img_opencv = info['img']

        succ = False
        while not succ:
            try:
                succ, base64_str = cv2.imencode('.jpg', img_opencv)
            except IOError:
                print("Transfer Error incurred in frame {}. Will redo. Don't worry. Just chill.".format(frame_num))
                pass

        file = base64.b64encode(base64_str)
        files = {'img': file, 'frame_num': frame_num}

        # 获取服务器返回的图片，字节流返回
        r = requests.post(url, files=files)
        result = r.content
        result = json.loads(s=result)
        print(result)

        return result['info'], result['people'], result['frame_num']

    def ReID(self):
        url = "http://www.wujiacloud.top:6060/photo"
        # url = "http://127.0.0.1:12345/photo"

        mot = r'video_frames'
        from glob import glob
        import os
        img_lists = glob(os.path.join(mot, '*.jpg'))
        fps = 0.0
        for idx, img_p in enumerate(img_lists):
            frame = cv2.imread(img_p)
            info = {'img': frame, 'frame_num': idx}
            succ, people, _ = detect_person_reid(info, url)

            # from utils.utils import plot_one_box
            if people:
                for p in people:
                    plot_one_box(p['pos'], frame, label=str(p['person_id']), color=[255, 255, 0])
            cv2.imshow('person search', frame)
            cv2.waitKey(10)

        r = requests.post("http://www.wujiacloud.top:6060/ping")
        print(r.content)

        r = requests.post("http://www.wujiacloud.top:6060/reinit_mot")
        print(r.content)

    def openFile(self):
        self.videoFileName = QFileDialog.getOpenFileName(self, 'Select Video File')
        self.file_name = list(self.videoFileName)[0]
        self.cap = cv2.VideoCapture(self.file_name)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.slider.setMinimum(0)
        self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.timer.start(1000/fps)
        # r = requests.post("http://www.wujiacloud.top:6060/ping")
        # print(r.content)

        r = requests.post("http://www.wujiacloud.top:6060/reinit_mot")
        print(r.content)

        r = requests.post("http://www.wujiacloud.top:6060/reinit_query")
        print(r.content)

    def openFile2(self):
        self.videoFileName2 = QFileDialog.getOpenFileName(self, 'Select Video File')
        self.file_name2 = list(self.videoFileName2)[0]
        self.cap2 = cv2.VideoCapture(self.file_name2)
        fps = self.cap2.get(cv2.CAP_PROP_FPS)
        self.slider2.setMinimum(0)
        self.slider2.setMaximum(int(self.cap2.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.timer2.start(1000/fps)
        # r = requests.post("http://www.wujiacloud.top:6060/ping")
        # print(r.content)

        r = requests.post("http://www.wujiacloud.top:6060/update_query")
        print(r.content)

    def playTimer(self):
        # start timer
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.timer.start(1000/fps)
        self.stopread = False

    def playTimer2(self):
        # start timer
        fps = self.cap2.get(cv2.CAP_PROP_FPS)
        self.timer2.start(1000 / fps)

    def stopTimer(self):
        # stop timer
        self.timer.stop()

    def stopTimer2(self):
        # stop timer
        self.timer2.stop()

    def videostop(self):
        #stop video
        self.timer.stop()
        self.slider.setValue(0)

    def videostop2(self):
        #stop video
        self.timer2.stop()
        self.slider2.setValue(0)

    def doubleplay(self):
        self.timer.stop()
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.timer.start(500/fps)

    def doubleplay2(self):
        self.timer2.stop()
        fps = self.cap2.get(cv2.CAP_PROP_FPS)
        self.timer2.start(500/fps)

    # def on_mouse(event, x, y, flags, param):
    #     global img, point1, point2
    #     img2 = img.copy()
    #     if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
    #         point1 = (x, y)
    #         cv2.circle(img2, point1, 10, (0, 255, 0), 5)
    #         cv2.imshow('image', img2)
    #     elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):  # 按住左键拖曳
    #         cv2.rectangle(img2, point1, (x, y), (255, 0, 0), 5)
    #         cv2.imshow('image', img2)
    #     elif event == cv2.EVENT_LBUTTONUP:  # 左键释放
    #         point2 = (x, y)
    #         cv2.rectangle(img2, point1, point2, (0, 0, 255), 5)
    #         cv2.imshow('image', img2)
    #         min_x = min(point1[0], point2[0])
    #         min_y = min(point1[1], point2[1])
    #         width = abs(point1[0] - point2[0])
    #         height = abs(point1[1] - point2[1])
    #         cut_img = img[min_y:min_y + height, min_x:min_x + width]
    #         cv2.imwrite('0001.jpg', cut_img)

    def readpics(self):
        directory_name = "Basketball/img"
        for filename in os.listdir(r"./" + directory_name):

            if (filename.endswith(".jpg")):
                image = cv2.imread(directory_name + "/" + filename)
                image = cv2.resize(image, (551, 551))
                cv2.imshow("image", image)

                # 每张图片的停留时间
                k = cv2.waitKey(1000)

                # 通过esc键终止程序
                if k == 27:
                    break

    def video2frame(self):
        # 第一个输入参数是包含视频片段的路径
        input_path = "/Users/danieltang/Downloads/player/video"
        # 第二个输入参数是设定每隔多少帧截取一帧
        frame_interval = 1
        # 列出文件夹下所有的视频文件
        filenames = os.listdir(input_path)
        # 获取文件夹名称
        video_prefix = input_path.split(os.sep)[-1]
        # 建立一个新的文件夹，名称为原文件夹名称后加上_frames
        frame_path = '{}_frames'.format(input_path)
        if not os.path.exists(frame_path):
            os.mkdir(frame_path)
        # 初始化一个VideoCapture对象
        cap = cv2.VideoCapture()
        # 遍历所有文件
        for filename in filenames:
            filepath = os.sep.join([input_path, filename])
            # VideoCapture::open函数可以从文件获取视频
            cap.open(filepath)
            # 获取视频帧数
            n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            for i in range(n_frames):
                ret, frame = cap.read()
                # 每隔frame_interval帧进行一次截屏操作
                if i % frame_interval == 0:
                    imagename = '{}_{}_{:0>6d}.jpg'.format(video_prefix, filename.split('.')[0], i)
                    imagepath = os.sep.join([frame_path, imagename])
                    print('exported {}!'.format(imagepath))
                    cv2.imwrite(imagepath, frame)
        # 执行结束释放资源
        cap.release()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseMove:
            if event.buttons() == QtCore.Qt.NoButton:
                pos = event.pos()
                self.edit.setText('x: %d, y: %d' % (pos.x(), pos.y()))
            else:
                pass # do other stuff
        return QtGui.QMainWindow.eventFilter(self, source, event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.timer.stop()
            self.stopread = True
            # self.display2.setText("鼠标左键点击！")
            print(event.pos().x(),event.pos().y())
            url = "http://www.wujiacloud.top:6060/mot"
        # global box_pos_x1, box_pos_x2, box_pos_y1, box_pos_y2, pedestrian_id
        for p in self.current_frame_p:
            box_pos_x1 = int(p['pos'][0])
            box_pos_x2 = int(p['pos'][2])
            box_pos_y1 = int(p['pos'][1])
            box_pos_y2 = int(p['pos'][3])
            pedestrian_id = str(p['person_id'])
            if box_pos_x1 < int(event.pos().x()) < box_pos_x2 and box_pos_y1 < int(event.pos().y()) < box_pos_y2:
        # import math
        # if math.sqrt((int(event.pos().x()) - box_pos_x)**2 + (int(event.pos().y()) - box_pos_y)**2) < 5.0:
                print('selected No.' + pedestrian_id)
            # self.current_frame_p
            # image = self.cap.read(int())
                plot_one_box(p['pos'], self.render_frame, label=str(p['person_id']), color=[255, 255, 0])
        self.timer.start()
        self.url = "http://www.wujiacloud.top:6060/query_id?id=1&id=3"
        # r = requests.get(url)
        # result = r.content
        # print(result)

    def Send(self):
        r = requests.get(self.url)
        result = r.content
        print(result)


app = QApplication(sys.argv)
widget = MainWindow()
widget.show()
sys.exit(app.exec_())
os.system("pause")