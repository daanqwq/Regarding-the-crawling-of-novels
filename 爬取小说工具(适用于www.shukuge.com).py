import requests
import re
import time
import sys
import os
from tqdm import tqdm
from pathlib import Path

def JingDuTiao(finish_tasks_number, tasks_number, EE=''):
    pbar = tqdm(
        total=tasks_number,
        desc="下载进度",
        unit="章",
        initial=finish_tasks_number,
        ncols=300,
        bar_format="{l_bar}{bar:50}{r_bar}",
        mininterval=1,
        smoothing=0.3
    )
    if EE:
        pbar.set_postfix_str(f"当前: {EE[:20]}" if len(EE) > 20 else f"当前: {EE}")
    return pbar

def get_chapter_content(url, max_retries=3):
    for retry in range(max_retries):
        try:
            with requests.get(url=f'http://www.shukuge.com{url}', timeout=5) as html:
                BiaoTi = re.search('<li class="active">(.*)</li>', html.text).group(1)
                contents = re.findall('&nbsp;&nbsp;&nbsp;&nbsp;(.*)<br />', html.text)
                last_line = re.search('&nbsp;&nbsp;&nbsp;&nbsp;(.*)</div>', html.text)
                if last_line:
                    contents.append(last_line.group(1))
                
                # 检测章节是否完整
                incomplete_markers = [
                    '正在手打中',
                    '请稍等片刻',
                    '内容更新后',
                    '请重新刷新页面',
                    '即可获取最新更新',
                    '全文字更新,牢记网址'
                ]
                
                is_incomplete = any(marker in line for line in contents for marker in incomplete_markers)
                
                # 清理内容
                cleaned_contents = []
                for line in contents:
                    # 移除网站广告和提示信息
                    if not any(marker in line for marker in incomplete_markers):
                        cleaned_line = re.sub(r'《.*?》', '', line)  # 移除书名标记
                        cleaned_line = re.sub(r'<.*?>', '', cleaned_line)  # 移除HTML标签
                        cleaned_line = cleaned_line.strip()
                        if cleaned_line:
                            cleaned_contents.append(cleaned_line)
                
                # 如果检测到不完整章节，添加提示
                if is_incomplete and cleaned_contents:
                    cleaned_contents.append("\n!!!此章内容不全，因为下载网站（www.shukuge.com）没有完整的小说内容!!!")
                elif is_incomplete and not cleaned_contents:
                    cleaned_contents.append("!!!本章内容尚未更新，请稍后再试或访问原网站查看!!!")
                
                return BiaoTi, cleaned_contents
                
        except KeyboardInterrupt:
            raise  # 直接抛出不重试
        except Exception as e:
            if retry == max_retries - 1:
                raise Exception(f"获取章节内容失败: {e}")
            time.sleep(retry + 1)

def main():
    try:
        # 获取脚本所在目录的绝对路径
        script_dir = Path(__file__).parent.absolute()
        
        # 用户输入处理
        while True:
            try:
                MuLu = input('请输入目录序号(仅支持http://www.shukuge.com)\n').strip()
                with requests.get(url=f'http://www.shukuge.com/book/{MuLu}/index.html') as html:
                    Da_BiaoTi = re.search('<h1>(.*)最新章节</h1>', html.text).group(1)
                    X_html = re.findall('<dd><a href=(.*) >', html.text)
                print(f"《{Da_BiaoTi}》共{len(X_html)}章")
                
                ZhangJie = int(input('从哪章开始？(默认1)\n') or 1) - 1
                if ZhangJie == 0:
                    # 使用脚本所在目录的路径创建文件
                    with open(script_dir / f'{Da_BiaoTi}.txt', 'w'):
                        pass
                break
            except KeyboardInterrupt:
                print('\n已取消输入')
                return
            except Exception as e:
                print(f'错误: {e}，请重试')

        # 下载处理
        pbar = None
        try:
            pbar = JingDuTiao(ZhangJie, len(X_html))
            # 使用脚本所在目录的路径打开文件
            with open(script_dir / f'{Da_BiaoTi}.txt', 'a', encoding='utf-8') as f:
                while ZhangJie < len(X_html):
                    try:
                        BiaoTi, NeiRon = get_chapter_content(X_html[ZhangJie][1:-1])
                        f.write('-'*12 + '\n' + BiaoTi + '\n')
                        for Duan in NeiRon:
                            f.write('    ' + re.sub('&nbsp;', ' ', Duan) + '\n')
                        
                        ZhangJie += 1
                        pbar.update(1)
                        pbar.set_postfix_str(f"章节: {BiaoTi[:20]}..." if len(BiaoTi) > 20 else f"章节: {BiaoTi}")
                        
                    except KeyboardInterrupt:
                        confirm = input('\n是否要退出？(Y/n) ').strip().lower()
                        if confirm == 'y' or confirm == '':
                            print('\n已退出')
                            return
                        else:
                            os.system('cls')
                        continue
                    except Exception as e:
                        print(f'\n章节{X_html[ZhangJie]}下载失败: {e}')
                        ZhangJie += 1
                        pbar.update(1) if pbar else None

            print('\n下载完成！')
        finally:
            if pbar:
                pbar.close()

    except KeyboardInterrupt:
        print('\n已退出')
    except Exception as e:
        print(f'\n程序异常: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
