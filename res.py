from PIL import Image
from typing import Union, Optional
from enum import Enum
from pathlib import Path
import requests
from furl import furl
from io import BytesIO
from zipfile import ZipFile

class Ratio:
    def __init__(self, w: int, h: int) -> 'Ratio':
        self.w = w
        self.h = h

    def raw(self) -> float:
        return self.w / float(self.h)
    
    def __repr__(self) -> str:
        return f'{self.w}to{self.h}'


class Canvas:
    class Scaling(Enum):
        UPSCALE = 0
        DOWNSCALE = 1
        PERSIST = 2

    class Snap(Enum):
        NORTH = 0
        EAST = 1
        SOUTH = 2
        WEST = 3
        CENTER = 4

    res = None
    name = ''

    def __init__(self, res: Optional[object] = None, name: Optional[str] = '') -> 'Canvas':
        self.res = res
        self.name = name

    @staticmethod
    def open(ref: Union[str, furl, bytes, Path, 'Canvas', Image.Image], name: Optional[str] = '') -> 'Canvas':
        return Canvas(res = next(
            func(ref = ref)
            for param, func in
            {
                str: Canvas._openString,
                furl: Canvas._openRequest,
                bytes: Canvas._openBytes,
                Path: Canvas._openPath,
                Canvas: Canvas._openCanvas,
                Image.Image: Canvas._openImage,
                object: Exception
            }.items()
            if isinstance(ref, param)
        ), name = name)

    def _openString(ref: str) -> Image.Image:
        return Image.open(ref)

    def _openRequest(ref: furl) -> Image.Image:
        with requests.get(
            ref.url
        ) as resp:
            return Image.open(
                BytesIO(resp.content)
            )

    def _openBytes(ref: bytes) -> Image.Image:
        return Image.open(ref)
    
    def _openPath(ref: Path) -> Image.Image:
        return Image.open(ref)

    def _openCanvas(ref: 'Canvas') -> Image.Image:
        return ref.getCopy()

    def _openImage(ref: Image.Image) -> Image.Image:
        return ref.copy()
    
    def getImage(self) -> Image.Image:
        return self.res
    
    def getBytes(self) -> bytes:
        with BytesIO() as buffer:
            self.getImage().save(buffer, 'PNG')
            return buffer.getvalue()
    
    def getCopy(self, name: Optional[str] = '') -> 'Canvas':
        return Canvas(res = self.getImage(), name = name)
    
    def getRatioRaw(self) -> float:
        return self.getImage().width / float(self.getImage().height)
        
    def getSize(self) -> tuple:
        return (self.getImage().width, self.getImage().height)
    
    def getName(self) -> str:
        return self.name
    
    def imageResize(self, width: int, height: int, snap: Optional[Snap] = Snap.CENTER) -> 'Canvas':
        self.res = self.getImage().resize((int(width), int(height)), Image.LANCZOS)
        return self

    def imageRescale(self, scale: Union[int, float]) -> 'Canvas':
        self.imageResize(*tuple([size * scale for size in self.getSize()]))
        return self

    def imageCrop(self) -> 'Canvas':
        self.getImage().crop()
        return self

    def imageReratio(self, ratio: Union[float, tuple, Ratio]) -> 'Canvas':
        ratioNew = ratio.raw()
        ratio = self.getRatioRaw()
        width, height = self.getSize()
        widthNew, heightNew = (None, None)
        
        if ratio > ratioNew:
            widthNew = int(ratioNew * height)
            offset = (width - widthNew) / 2
            resize = (offset, 0, width - offset, height)
        elif ratio < ratioNew:
            heightNew = int(width / ratioNew)
            offset = (height - heightNew) / 2
            resize = (0, offset, width, height - offset)
        else:
            return self

        self.res = self.getImage().crop(resize).resize((widthNew or width, heightNew or height), Image.ANTIALIAS)

        return self


    def scale(self):
        pass


def main():
    ratios = [Ratio(2, 1), Ratio(16, 9), Ratio(1, 1)]
    scales = [1.0, 0.75, 0.5]

    canvas = Canvas.open(ref = furl(url = 'https://cdn.discordapp.com/attachments/1105364473872650290/1107872855196188732/Ghosti_Impressionism_of_forest_with_deer_in_the_middle_natural__37536139-d9a3-49a9-b894-e513395f063c.png'))
    with ZipFile('test.zip', 'w') as file:
        for ratio in ratios:
            for scale in scales:
                rimg = canvas.getCopy(f'pic_{ratio}_x{scale}').imageReratio(ratio).imageRescale(scale)
                file.writestr(f'{rimg.getName()}.png', rimg.getBytes())


if __name__ == '__main__':
    main()
