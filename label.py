from adafruit_epd.epd import Adafruit_EPD
import adafruit_imageload
import fontlarge
import fontsmall
import time

PALETTE = (Adafruit_EPD.BLACK, Adafruit_EPD.RED, Adafruit_EPD.WHITE)


def bg_image(display, image):
    print("IMAGE", image)
    image, p = adafruit_imageload.load(image)
    range_x = range(image.width)
    range_y = range(image.height)

    display.fill(Adafruit_EPD.WHITE)
    display.display()

    for x in range_x:
        for y in range_y:
            color = PALETTE[image[x, y]]
            if color != Adafruit_EPD.WHITE:
                display.pixel(x, y, color)



def printtext(display, x, y, text, color, bg_color, font=fontlarge, shadow_offset=5):
    offset_x = 0
    print("print:", text)
    for char in text:
        data, h, w = font.get_ch(char)
        bytes_per_col = (h - 1) // 8 + 1
        for row in range(h):
            for col in range(w):
                byte = data[col * bytes_per_col + row // 8]
                bit = (byte & (1 << (row % 8))) > 0
                if bit:
                    display.pixel(x + offset_x + col, y + row, color)
                    if bg_color:
                        display.pixel(x + offset_x + col + shadow_offset, y + row + shadow_offset, bg_color)
        offset_x += w

def large(display, x, y, text, color, bg_color):
    printtext(display, x, y, text, color, bg_color, fontlarge)


def small(display, x, y, text, color, bg_color):
    printtext(display, x, y, text, color, bg_color, fontsmall, 2)
