#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
import os, sys, io
import threading
import kivy
kivy.require('1.9.0')
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from hoverable import HoverBehavior
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.config import ConfigParser, Config
from kivy.graphics import Line
import configparser
from kivy.properties import StringProperty, NumericProperty
from hpopup import Copy, Move, Remove, Rename, Box
from ffpeglib import Boxd, MovieBox
from kivy.core.image import Image as CoreImage
from functools import partial
from datetime import timedelta
from ffpeglib import VideoStream
from kivy.graphics import *
# from PIL import Image, ImageDraw

__author__='hernani'
__email__ = 'afhernani@gmail.com'
__apply__ = 'kvcomic with ffpyplayer'
__version__ = 2.1


class ImageR(Image):
    angle = NumericProperty(0)

    def __init__(self, angle=180, **kwargs):
        super(ImageR, self).__init__(**kwargs)
        self.angle = angle


class Splitfloat(HoverBehavior, ImageR):
    def __init__(self, url, **kwargs):
        self.selected = None
        self.url = None if url is None else url
        self.video = self.state = None
        self.duration = self.loop_time = self.interval = 0.0
        self.num_visionado = 22
        self.thr, self.image, self.animation = None, None, False

        super(Splitfloat, self).__init__(**kwargs)
        
        if self.url:
            self.video = VideoStream(source=self.url)
            self.duration = self.video.duration
            self.loop_time = self.duration/(self.num_visionado + 1)
            self.interval = self.loop_time
            self.thr = threading.Thread(target=self.init_image, args=(self.url,), daemon=True)
            self.thr.start()
            # self.video.toggle_pause()        
            self.tooltip = Tooltip(text=str(timedelta(seconds=self.duration)))

    def init_image(self, url):
        import time
        if self.video.pause: self.video.toggle_pause()
        pts = self.interval
        if self.interval >= self.duration:
            pts = self.loop_time
        # print('pts ini:', url,  pts)
        self.video.seek(pts=pts, relative=True, accurate=False)
        time.sleep(0.4)
        # Clock.schedule_once(self.callback, 2)
        tarea = True
        while tarea:
            try:
                self.state, posission, self.image = self.video.get_frame()
                # print('ROUND:', url, round(pts, 2), '/', round(posission, 2))
                if self.state == 'eof':
                    self.video.seek(pts=pts, relative=False, accurate=False)
                    time.sleep(0.2)
                elif self.video.pause:
                    self.video.toggle_pause()
                elif self.image:
                    if posission < self.loop_time:
                        time.sleep(0.2)
                    else:
                        tarea = False
            except Exception as e:
                print('>> init_image -->', str(e.args))
        self.video.toggle_pause()
        self.interval = posission
        if self.video:
            self.video = None
        Clock.schedule_once(partial(self.push_image, self.image))

    def callback(self, dt):
        Clock.unschedule(self.callback)
        pass

    def __del__(self):
        ''' body of destructor '''
        self.animation = False
        Clock.unschedule(self.my_anim)
        if self.video: del self.video

    @mainthread
    def push_image(self, image, *args):
        from kivy.graphics.texture import Texture
        # from ffpyplayer import Image as FFpyImage
        self.image = None if image is None else image
        if self.image is None:
            from utility import CreateImg
            self.image =  CreateImg()
            image_bytes = io.BytesIO()
            self.image.save(image_bytes, 'png')
            image_bytes.seek(0)
            self._coreimage = CoreImage(image_bytes, ext='png')
            self.texture = self._coreimage.texture
        else:
            size = self.image.get_size()
            texture = Texture.create(size=size, colorfmt='rgb', bufferfmt='ubyte')
            # self.image.get_linesizes(keep_align=True)
            arr = self.image.to_memoryview()[0] # array image
            if arr is None:
                return
            # img = FFpyImage(plane_buffers=[self.image.to_bytearray()], pix_fmt='rgb24', size=size)
            # datos = self.image.to_bytearray()
            # image_bytes = io.BytesIO(arr)
            # image_bytes.seek(0)
            # self._coreimage = CoreImage(image_bytes, ext='png')
            # self._coreimage.save('prueba.png')
            # buf = b''.join(map(chr, arr)) # array to a ubyte string
            texture.blit_buffer(arr)
            # im = CoreImage(texture)
            self.texture = texture
            # self.texture = self._coreimage.texture
            

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        self.tooltip.pos = pos
        Clock.unschedule(self.display_tooltip) # cancel scheduled event since I moved the cursor
        self.close_tooltip() # close if it's opened
        if self.collide_point(*self.to_widget(*pos)):
            Clock.schedule_once(self.display_tooltip, 1)
        return super(Splitfloat, self).on_mouse_pos(*args)
            
    def close_tooltip(self, *args):
        Window.remove_widget(self.tooltip)
    
    def display_tooltip(self, *args):
        Window.add_widget(self.tooltip)

    def on_press(self):
        # self.source = 'atlas://data/images/defaulttheme/checkbox_on'
        print('on_press')
        pass

    def on_release(self):
        # self.source = 'atlas://data/images/defaulttheme/checkbox_off'
        pass

    def on_touch_down(self, touch):
        # (x, y)=self.to_widget(touch.x, touch.y)
        ''' if self.collide_point(x, y):
            if touch.is_double_tap:
                print('double touch', 'action here', self.source)
                return True '''
        if self.collide_point(touch.x, touch.y):
            if not self.selected:
                self.select()
            else:
                self.unselect()
            self.touched = True
            if touch.is_double_tap:
                print('double:', self.source)
                from utility import lunch_ffplay
                lunch_ffplay(self.url)
            return True
        return super(Splitfloat, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        # x, y = touch.x, touch.y
        # (x, y)=self.parent.to_parent(touch.x, touch.y)  
        (x, y)=self.to_widget(touch.x, touch.y)
        # print(x, y)
        if self.collide_point(touch.x, touch.y):
            print('true')
            return True
        return super(Splitfloat, self).on_touch_move(touch)

    def on_enter(self, *args):
        print("You are in, though this point", self.border_point, self.source)
        # self.anim_delay= 1
        Clock.unschedule(self.my_anim)
        # si el video está en play lo detenemos
        '''if not self.video.pause:
            self.video.toggle_pause()'''
        if self.video and self.thr.is_alive:
            print('on_enter, animation, self.thr is alive')
            
        if self.video is None:
            print('on enter,  animation')
            self.animation = True
            Clock.schedule_once(self.my_anim)
        
        
    def my_anim(self, dts):
        self.thr = threading.Thread(target=self.start_animation, args=(self.url,), daemon=True)
        self.thr.start()
        
    def start_animation(self, url):
        # Falta: comprobar la url -
        from time import sleep
        self.video = VideoStream(source=self.url)
        posission = 0.0
        if self.video.pause: self.video.toggle_pause()
        print(self.url, '->', 'interval:', self.interval, 'loop:', self.loop_time)    
        if self.interval >= self.duration or self.state=='eof':
            self.video.seek(pts=self.loop_time, relative=False, accurate=False)
            self.interval = self.loop_time
            sleep(0.5)
        else:
            self.video.seek(pts=self.interval, relative=False, accurate=False)
            sleep(0.5)
        while self.animation and self.video:    # while loop video animation
            self.image = None   
            self.state, posission, self.image = self.video.get_frame()
            if self.state == 'eof':
                self.video.seek(pts=self.loop_time, relative=False, accurate=False)
                self.interval = self.loop_time
                sleep(0.2)
            elif posission < self.interval:
                sleep(0.1)
                continue
            #print('state:', self.state, 'interval:', self.interval)
            elif self.image:
                Clock.schedule_once(partial(self.push_image, self.image))
            # partial(self.push_image, image)
            # self.push_image(image=image)
            sleep(self.state)
        self.interval = posission + self.loop_time
        print('set interval:', self.interval)
        # self.video.player.close_player()
        if self.video:
            self.video = None

    def on_leave(self, *args):
        print("You left through this point", self.border_point, self.source)
        # self.anim_delay= -1
        # if self.thr.isAlive:
        self.animation = False
        self.thr.join()
        # self.video.toggle_pause()
            

    def select(self):
        print('select()', self.top)
        if not self.selected:
            self.ix = self.center_x
            self.iy = self.center_y
            with self.canvas.before:
                # self.Color(rgb=(1,0,0))
                self.selected = Line(rectangle=
                    (self.x, self.y, self.width, self.height), dash_offset=2, color=(1,0,0), width=10)

    def unselect(self):
        print('unselect()')
        if self.selected:
            self.canvas.before.remove(self.selected)
            self.selected = None


class Tooltip(Label):
    pass
   
    
Builder.load_string('''
<ImageR>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: self.angle
            axis: (0, 0, 1)
            origin: self.center
    canvas.after:
        PopMatrix

<Tooltip>:
    size_hint: None, None
    size: self.texture_size[0]+5, self.texture_size[1]+5
    canvas.before:
        Color:
            rgb: 0.2, 0.2, 0.2
        Rectangle:
            size: self.size
            pos: self.pos

<ContentSplits>:
    orientation:'vertical'
    ScrollView:
        BoxLayout:
            id:box
            orientation:'horizontal'
            height: self.minimum_height
            size_hint_x:None
            width: self.minimum_width
            padding: '20dp', '20dp'
            spacing: '20dp'
    BoxLayout:
        height:'30sp'
        size_hint_y:None
        Button:
            text:'Open'
            size_hint_x:None
            width: '60sp'
            on_release:app.get_running_app().show_load()
        Button:
            text:'Move'
            size_hint_x:None
            width:'60sp'
            on_release:app.get_running_app().move_selected()
        Button:
            text:'Copy'
            size_hint_x:None
            width:'60sp'
            on_release:app.get_running_app().copy_selected()
        Label:
            id:lbnota
            text:'...'
            size_hint_x:None
            width: '60sp'
<Splitfloat>:
    anim_delay: 1 if self.hovered else -1
    allow_stretch: True
    # pos: 200,200
    # size_hint: None, None
    size: '300sp', '200sp'
    size_hint_x: None
    font_size: '20dp'
    #Rotate:
    #    angle:180
    #    origin: self.center
    # height: '300dp'
    # with: '300dp'
    # canvas.before:
    #    Rotate:
    #        angle: 180
    #Image:
    #    pos: root.pos
    #    size: root.size
    #    source: 'bbw.gif'
<LoadDialog>:
    BoxLayout:
        size: root.size
        pos: root.pos
        orientation:'vertical'
        FileChooserListView:
            id: filechooser
            multiselect: True
            path:'.'
        BoxLayout:
            size_hint_y: None
            height:sp(30)
            Button:
                text:'Cancel'
                on_release:root.cancel()
            Button:
                text:'Load'
                on_release: root.load(filechooser.path, filechooser.selection)
    
''')


class ContentSplits(BoxLayout):
    files=[]
    def __init__(self, files=[], **kwargs):
        super(ContentSplits, self).__init__(**kwargs)
        self.files = files
        for file in self.files:
            # img = Image(source=file, anim_delay=1)
            self.ids.box.add_widget(Splitfloat(url=file, anim_delay=1))
    
    def addfile(self):
        print('addfile:', self.files)
        box = BoxLayout(orientation='vertical',padding=10,spacing=10)
        botones = BoxLayout(padding=10,spacing=10, size_hint_y=None, height=30)
        
        self.filechooser = FileChooserListView()
        # self.filechooser.height = 400 # this is a bit ugly...
        self.filechooser.path='.'

        box.add_widget(self.filechooser)
        
        pop = Popup(title='Select Directory',content=box,size_hint=(None,None),
                    size=(400,600))

        si = Button(text='Si',on_release=self.on_load, height='30dp', width='20dp')
        no = Button(text='No',on_release=pop.dismiss, height='30dp', width='20dp')
        botones.add_widget(si)
        botones.add_widget(no)
        box.add_widget(botones)

        pop.open()
        # print('select', self.filechooser.selection)
        
    

from kivy.properties import ObjectProperty

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    
class SampleApp(App):
    # stop = threading.Event()
    setingfile = 'seting.ini'
    title ='Splitfloat'
    path_job = StringProperty(None)
    tr = None # tarea de carga de ficheros
    isloadfiles = True # cargar ficheros from directorio a true 
    
    def build(self):
        self.files=[]
        self.box = ContentSplits(files=self.files)
        # box.ids.box.add_widget(Splitfloat(source='mica.gif',anim_delay= 1))
        self.get_init_status()
        return self.box

    def selected_splitfloat(self, *args):
        '''busca los splitfloats selecioado y devuelve una lista con los objetos'''
        boxes = self.box.ids.box
        childrens= boxes.children[:]
        selected =[]
        for child in childrens:
            if child.selected:
                selected.append(child)
                child.unselect()
        return selected

    def copy_selected(self, *args):
        '''copy splitfloat to ... '''
        selected = self.selected_splitfloat()
        all_archives = self._createlistselected(selected=selected)
        if self.path_job is None:
            self.path_job =os.path.dirname(all_archives[0])
        for item in all_archives:
            print('selected ->>', item)
        Copy(files=all_archives, on_dismiss=self.my_callback, path=self.path_job)

    def move_selected(self, *args):
        '''move splitfloats to ...'''
        selected = self.selected_splitfloat()
        all_archives = self._createlistselected(selected=selected)
        if self.path_job is None:
            self.path_job =os.path.dirname(all_archives[0])
        for item in all_archives:
            print('selected ->>', item)
        Move(files=all_archives, on_dismiss=self.my_callback, path=self.path_job)
        for child in selected: self.box.ids.box.remove_widget(child)

    def my_callback(self, instance):
        self.path_job = instance.path

    def _createlistselected(self, selected=[])->[]:
        todos_los_archivos =  []
        for item in selected:
            todos_los_archivos.append(item.url)
        return todos_los_archivos

    def dismiss_popup(self, *args):
        self.popup.dismiss()
    
    def show_load(self):
        contenido=LoadDialog(load=self.load, cancel=self.dismiss_popup)
        contenido.ids.filechooser.path = self.dirpathmovies
        self.popup= Popup(title='Selct Directory', content=contenido, size_hint=(.9,.9))
        self.popup.open()

    def load(self, path, filenames):
        self.popup.dismiss()
        self.dirpathmovies = path
        # for filename in filenames:
        #    with open(os.path.join(path, filename)) as cadena:
        #        self.files.append(filename)
        # print('files:', self.files)
        print('path:', path, 'filenames:', filenames)
        self.files=[]
        if self.tr:
            self.isloadfiles = False
            while self.tr.is_alive(): print('.', end='')
            print('ended load')
            boxes = self.box.ids.box
            childrens= boxes.children[:]
            for child in childrens:
                del child
            self.isloadfiles = True
        self.load_thread()
        # threading.Thread(target=self.load_thread, daemon=True).start()
        # pasando con argumentos, .
        # threading.Thread(target=self.load_thread, args=(argumeto,), daemon=True).start()

    def load_thread(self, *args):
        from functools import partial
        self.total = 0
        dirpathmovies = self.dirpathmovies
        title = 'Splitfloat :: ' + dirpathmovies
        print('dirpathmovies:', dirpathmovies)
        exten = ('.mp4', '.flv', '.avi', '.mpg', '.mkv', 
                 '.webm', '.ts', '.mov', '.MP4', '.FLV',
                 '.MPG', '.AVI', '.MKV', 'WEBM', '.MOV',
                 '.TS')
        self.box.ids.box.clear_widgets()
        if os.path.exists(dirpathmovies):
            for fe in os.listdir(dirpathmovies):
                if fe.endswith(exten):
                    fex = os.path.abspath(os.path.join(dirpathmovies, fe))
                    # print(fex)
                    self.files.append(fex)
                    # Clock.schedule_once(partial(self.update_box_imagen, str(fex)), 0.5)
                    # self.box.ids.box.add_widget(Splitfloat(source=fex, anim_delay= 1))
        self.title = title + ' :: ' + str(len(self.files))
        Window.set_title(self.title)
        self.tr = threading.Thread(target=self.start_load_thread, args=(self.files,), daemon=True)
        self.tr.start()

    def start_load_thread(self, files=[]):
        from time import sleep
        try:
            for file in files:
                self.update_box_imagen(file)
                sleep(0.2)
                if not self.isloadfiles: break
        except:
            print('exception in start load thread from app')
    
    total = 0
    
    @mainthread
    def update_box_imagen(self, file, *largs):
        self.box.ids.box.add_widget(Splitfloat(url=file, anim_delay= -1))
        # self.title = 'Splitfloat :: ' + self.dirpathmovies + ' :: ' + str(len(self.files))
        # print('>> long: ', title)
        self.total += 1
        self.box.ids.lbnota.text = str(self.total)

    def get_init_status(self):
        '''
        extract init status of app
        Return:
        '''
        if not os.path.exists(self.setingfile):
            return
        config = configparser.RawConfigParser()
        config.read(self.setingfile)
        self.dirpathmovies = config.get('Setings', 'dirpathmovies')
        if os.path.exists(self.dirpathmovies):
            # inicializa la lista con directorio duardao
            # threading.Thread(target=self.load_thread, daemon=True).start()
            self.load_thread()
        else:
            self.dirpathmovies = os.getcwd()

    def on_stop(self):
        '''
        write init status of app
        Return:
        '''
        config = configparser.RawConfigParser()
        config.add_section('Setings')
        config.set('Setings', 'dirpathmovies', self.dirpathmovies)
        config.set('Setings', 'sizewindow', self.sizewindow)
        with open(self.setingfile, 'w') as configfile:
            config.write(configfile)
        print('Write config file')
        # vamos a detener todas las tareas
        boxes = self.box.ids.box
        childrens= boxes.children[:]
        for child in childrens:
            del child
    
    sizewindow =''
    
    def on_resize(self, instancie, width, height):
        '''Event called when the window is resized'''
        print(f'window.size {str(width)}, {str(height)}')
        print(f'instancie: {instancie.top}, {instancie.left}')
        self.sizewindow = str(width)+'x'+ str(height) + 'x' + str(instancie.top) + 'x' + str(instancie.left)
        print('variable: '+ self.sizewindow)
        
    def get_sizewindow(self, cadena):
        '''descomponer la cadena de dimensiones de la ventana'''
        return cadena.split('x')

    from kivy.core.window import Window

    def on_start(self, **kvargs):
        ''' lunch after build and start window '''
        Window.bind(on_resize=self.on_resize)
        # Window.bind(on_motion=self.on_motion_thumbapp)
        # Window.bind(on_draw=self.on_draw_thumbapp)
        Window.bind(on_request_close=self.on_request_close)
        # self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        Window.bind(on_keyboard=self.on_keyboard)
        # print('on_start')
        if not os.path.exists(self.setingfile):
            return
        config = configparser.RawConfigParser()
        config.read(self.setingfile)
        try:
            self.sizewindow = config.get('Setings', 'sizewindow')
            w, h, t, l = self.get_sizewindow(self.sizewindow)
            # print(w, h, t, l)
            Window.size = (int(w), int(h))
            Window.Top = int(t)
            Window.left = int(l)
        except Exception:
            print('exception load sizewindow')

    def on_request_close(self, *args):
        self.textpopup(title='Exit', text='Are you sure?')
        return True

    def textpopup(self, title='', text=''):
        """Open the pop-up with the name.
 
        :param title: title of the pop-up to open
        :type title: str
        :param text: main text of the pop-up to open
        :type text: str
        :rtype: None
        """
        box = BoxLayout(orientation='vertical')
        box.add_widget(Label(text=text))
        mybutton = Button(text='OK', size_hint=(1, 0.25))
        box.add_widget(mybutton)
        popup = Popup(title=title, content=box, size_hint=(None, None), size=(300, 200))
        mybutton.bind(on_release=self.stop) # manda detener la aplicación
        popup.open()

    def on_keyboard(self, keyboard, key, text, modifiers, *args):
        print(f'{keyboard}, {key}, {text}, {modifiers}, {args}')
        return True


if __name__ == '__main__':
    SampleApp().run()

