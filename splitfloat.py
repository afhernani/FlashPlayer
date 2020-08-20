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
from kivy.properties import StringProperty
from hpopup import Copy, Move, Remove, Rename, Box
from ffpeglib import Boxd, MovieBox
from kivy.core.image import Image as CoreImage
from functools import partial
from datetime import timedelta

__author__='hernani'
__email__ = 'afhernani@gmail.com'
__apply__ = 'kvcomic app for gif about viedo in carpet'
__version__ = 0.1

class Splitfloat(HoverBehavior, Image):
    def __init__(self, url, **kwargs):
        self.selected = None
        self.url = None if url is None else url
        self.moviebox = None
        self.duration = self.loop_time = self.interval = 0.0
        self.num_visionado = 26
        self.thr, self.animation = None, False
        super(Splitfloat, self).__init__(**kwargs)
        if self.url:
            self.moviebox = MovieBox(source=self.url)
            self.duration = self.moviebox.datos['time']
            self.loop_time = self.duration/(self.num_visionado + 1)
            self.interval = self.loop_time
            image = self.moviebox.extract_image(time=self.loop_time)
            self.push_image(image=image)
            self.tooltip = Tooltip(text=str(timedelta(seconds=self.duration)))

    def __del__(self):
        ''' body of destructor '''
        self.automation = False
        Clock.unschedule(self.my_anim)

    @mainthread
    def push_image(self, image, *args):
        self.image = None if image is None else image
        if self.image is None:
            self.image = self.moviebox.CreateImg()
        image_bytes = io.BytesIO()
        self.image.save(image_bytes, 'png')
        image_bytes.seek(0)
        self._coreimage = CoreImage(image_bytes, ext='png')
        self.texture = self._coreimage.texture

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
        if self.collide_point(x, y):
            print('true')
            return True
        return super(Splitfloat, self).on_touch_move(touch)

    def on_enter(self, *args):
        print("You are in, though this point", self.border_point, self.source)
        # self.anim_delay= 1
        Clock.unschedule(self.my_anim)
        self.animation = True
        Clock.schedule_once(self.my_anim, 1.5)
        
        
    def my_anim(self, dts):
        self.thr = threading.Thread(target=self.start_animation, args=(self.url,), daemon=True)
        self.thr.start()
        
    def start_animation(self, url):
        # Falta: comprobar la url -
        from time import sleep
        while self.animation:    
            self.interval += self.loop_time
            if self.interval > self.duration-self.loop_time:
                self.interval = self.loop_time
            image = self.moviebox.extract_image(time=self.interval)
            Clock.schedule_once(partial(self.push_image, image))
            # partial(self.push_image, image)
            # self.push_image(image=image)
            sleep(0.8)

    def on_leave(self, *args):
        print("You left through this point", self.border_point, self.source)
        # self.anim_delay= -1
        # if self.thr.isAlive:
        self.animation = False
            

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
    # height: '300dp'
    # with: '300dp'
    font_size: '20dp'
    # canvas.before:
    #    Color:
    #        rgb: 1,1,1
    #    Rectangle:
    #        size: self.size
    #        pos: self.pos
    # Image:
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
        self.isloadfiles = False
        while self.tr.is_alive(): print('.', end='')
        print('ended load')
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
                sleep(1.5)
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

