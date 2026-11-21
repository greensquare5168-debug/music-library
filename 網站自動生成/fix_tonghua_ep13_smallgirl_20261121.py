#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOYO童話世界 第13集「小小姑娘」補三段哥哥姐姐：Downside Up、Walkin' And Whistlin'、Foxy Trot
（各自獨立一個 哥哥姐姐 框；片尾曲留在最後）
幂等：已有 3 個哥哥姐姐框則跳過。
"""
import re, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(BASE, '罐頭音樂研究所/yoyotv/yoyo童話世界/yoyo童話世界-第13集-鴨媽媽的寶貝蛋小小姑娘/index.html')

LI_DOWN = ('<li><a href="https://www.youtube.com/watch?v=Ts2A3VXF5S4" target="_blank" rel="noopener">Downside Up - Jonathan Jans</a>'
           '<span class="lbl">（PML-148 Comicals）</span>'
           '<a class="same" href="/music-library/%E7%BD%90%E9%A0%AD%E9%9F%B3%E6%A8%82%E7%A0%94%E7%A9%B6%E6%89%80/%E5%9C%96%E6%9B%B8%E9%A4%A8%E9%9F%B3%E6%A8%82/parry/pml148-comicals/downside-up-jonathan-jans/" '
           'title="查看同使用作品" style="margin-left:6px;font-size:15px;line-height:1;color:#8a97a8;text-decoration:none">↗</a></li>')

LI_WALK = ('<li><a href="https://www.youtube.com/watch?v=eCZGElr80Bo" target="_blank" rel="noopener">Walkin\' And Whistlin\' - Harry Gordon Forbes</a>'
           '<span class="lbl">（PML-016 The Comedy Collection）</span>'
           '<a class="same" href="/music-library/%E7%BD%90%E9%A0%AD%E9%9F%B3%E6%A8%82%E7%A0%94%E7%A9%B6%E6%89%80/%E5%9C%96%E6%9B%B8%E9%A4%A8%E9%9F%B3%E6%A8%82/parry/pml016-the-comedy-collection/walkin-and-whistlin-harry-gordon-forbes/" '
           'title="查看同使用作品" style="margin-left:6px;font-size:15px;line-height:1;color:#8a97a8;text-decoration:none">↗</a></li>')

LI_FOXY = ('<li><a href="https://www.youtube.com/watch?v=jUy6jLlD5Zw" target="_blank" rel="noopener">Foxy Trot - James Clarke</a>'
           '<span class="lbl">（PML-148 Comicals）</span>'
           '<a class="same" href="/music-library/%E7%BD%90%E9%A0%AD%E9%9F%B3%E6%A8%82%E7%A0%94%E7%A9%B6%E6%89%80/%E5%9C%96%E6%9B%B8%E9%A4%A8%E9%9F%B3%E6%A8%82/parry/pml148-comicals/foxy-trot-james-clarke/" '
           'title="查看同使用作品" style="margin-left:6px;font-size:15px;line-height:1;color:#8a97a8;text-decoration:none">↗</a></li>')


def main():
    h = open(PAGE, encoding='utf-8').read()
    if '>Downside Up - Jonathan Jans<' in h and '>Foxy Trot - James Clarke<' in h:
        print('三首已在頁面，跳過')
        return

    # 取得「小小姑娘」區段的片尾 ul 內容（空白 li + 片尾 li）
    i = h.find('data-label="小小姑娘"')
    if i < 0:
        print('找不到 小小姑娘 區段')
        sys.exit(1)
    j = h.find('</main>', i)
    seg = h[i:j]
    ul = re.search(r'<ul class="entries">(.*?)</ul>', seg, re.S)
    tail_lis = re.findall(r'<li[^>]*>.*?</li>', ul.group(1), re.S)
    keep = ''.join(tail_lis)  # 空白 li + 片尾 li

    SM = '<div class="unit sm" data-label="哥哥姐姐">哥哥姐姐</div>'
    BL = '<div class="blankline">&nbsp;</div>'
    new_seg = ('data-label="小小姑娘">小小姑娘</div> ' + SM +
               ' <ul class="entries">' + LI_DOWN + '</ul>' + BL +
               SM + ' <ul class="entries">' + LI_WALK + '</ul>' + BL +
               SM + ' <ul class="entries">' + LI_FOXY + '</ul>' + BL +
               '<ul class="entries">' + keep + '</ul>')

    new = h[:i] + new_seg + h[j:]
    open(PAGE, 'w', encoding='utf-8').write(new)
    print('已補 小小姑娘 三段哥哥姐姐：Downside Up／Walkin\' And Whistlin\'／Foxy Trot')


if __name__ == '__main__':
    main()
