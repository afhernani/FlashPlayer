#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ffpyplayer.player import MediaPlayer
from ffpyplayer.pic import Image as PicImage
from ffpyplayer import pic
from PIL import Image as PilImage
import time
import os

__author__ = 'Hernani Aleman Ferraz'
__email__ = 'afhernani@gmail.com'
__apply__ = 'Flash - player, kvcomic'
__version__ = '2'
__all__ = ('VideoStream')

class VideoStream:
    def __init__(self, source=None):
        ff_opts = {'paused': True, 'autoexit': False, 
                   'autorotate': False, 'volume': 0.5,
                   'filter_threads': 4 }  # Audio options
        self.source = source
        # Open the video source
        self.player = MediaPlayer(source, ff_opts=ff_opts)
        # TODO: colocar pausa de tiempo para cargas mediaplayer y obtener los datos
        # conseguir el frame rate para la sincronizacion self.dalay
        while self.player.get_metadata()['src_vid_size'] == (0, 0):
            time.sleep(0.01)
        self.metadata  = self.player.get_metadata()
        print('data -->', self.metadata)
        self.f_rate = int(self.metadata['frame_rate'][0]/self.metadata['frame_rate'][1])
        print('delay -> ', self.f_rate)
        self.w, self.h = self.metadata['src_vid_size']
        print('WxH -> ', self.w, self.h)
        self.pts = self.player.get_pts() # Returns the elapsed play time. float
        print('pts ->', self.pts)
        self.duration = self.metadata['duration']
        print('duration', self.duration)
        self.pause = self.player.get_pause() # Returns whether the player is paused.
        print('pause ->', self.pause)
        self.volume = self.player.get_volume() # Returns the volume of the audio. loat: A value between 0.0 - 1.0
        print('volume ->', self.volume)
        self.player.toggle_pause() # Toggles -alterna- the player’s pause state
        self.pause = self.player.get_pause()
        # self.player.set_pause(False) # auses or un-pauses the file. state: bool
        cond = True
        while cond:
            self.l_frame, self.val = self.player.get_frame()
            if self.val == 'eof':
                print('can not open source: ', source)
                break
            elif self.l_frame is None:
                time.sleep(0.01)
            else:
                self._imagen, self.pts = self.l_frame
                print('pts ->', self.pts)
                # arr = self._imagen.to_memoryview()[0] # array image
                # self.imagen = Image.frombytes("RGB", self.original_size, arr.memview)
                # self.imagen.show()
                cond = False

    def get_frame(self):
        '''
        Return valores:
            val : 'eof' or 'pause' 
            pts : time location aduio imagen.
            imagen : frame image
        Return (val, t, imagen)
        '''
        self.l_frame, self.val = self.player.get_frame()
        if self.val == 'eof':
            # condicion final fichero, salimos if and while
            # self.player.toggle_pause() # ponemos en pause
            return self.val, 0.0, None 
        elif self.l_frame is None:
            time.sleep(0.01)
            return self.val, 0.0, None
        else:
            self._imagen, self.pts = self.l_frame
            return self.val, self.pts, self._imagen

    def toggle_pause(self):
        '''
            Function: toggle_pause
        '''
        try: # Stopping audio
            self.player.toggle_pause()
            self.pause = self.player.get_pause()
        except:
            pass
    
    def seek(self, pts, relative=True, seek_by_bytes='auto', accurate=True):
        '''
        Seeks to the desired timepoint as close as possible while not exceeding 
        that time.

            Parameters
                pts: float
                    The timestamp to seek to (in seconds).
                relative: bool
                    Whether the pts parameter is interpreted as the 
                    time offset from the current stream position 
                    (can be negative if True).
                seek_by_bytes: bool or 'auto'
                    Whether we seek based on the position in bytes 
                    or in time. In some instances seeking by bytes may 
                    be more accurate (don’t ask me which). If 'auto', 
                    the default, it is automatically decided based 
                    on the media.
                accurate: bool
                    Whether to do finer seeking if we didn’t seek directly
                    to the requested frame. This is likely to be slower 
                    because after the coarser seek, we have to walk through 
                    the frames until the requested frame is reached. 
                    If paused or we reached eof this is ignored. Defaults to True.
        '''
        self.player.seek(pts, relative=relative, seek_by_bytes=seek_by_bytes, accurate=accurate)

    def snapshot(self, road=None):
        '''
        get current frame
        '''
        img = self.l_frame[0]
        if img is not None:
            size = img.get_size()
            arr = img.to_memoryview()[0] # array image
            img = PilImage.frombytes("RGB", size, arr.memview)
            # vamos a guardar esto.
            time_str = time.strftime("-%H-%M-%S")
            frame_name  = f"frame-{time_str}.jpg"
            if not road:
                ruta = os.path.dirname(self.source)
                name_out = os.path.join(ruta, frame_name)
            else:
                name_out = os.path.join(road, frame_name)
            img.save(name_out)
        

    # Release the video source when the object is destroyed
    def __del__(self):
        self.player.close_player()
        # print('__del__', 'destructor videostream')


if __name__ == '__main__':
    video = VideoStream('_Work/tem.mp4')
