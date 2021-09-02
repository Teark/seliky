*** Settings ***
Library            WebDriver2.py

*** Variables ***
# 元素定位和界面信息
${baidu_url}  http://www.baidu.com
${baidu_fanyi_url}  "https://fanyi.baidu.com/#zh/en/"
${search_box}  id=kw
@{search_button}    id=wrong id     //@class=wrong xpath    id=su   css=wrong css    # 弹性定位：列表中只要有一个元素是对的，就能定位到
@{search_words}     小唐       小李      小刘


*** Test Cases ***
# 百度搜索测试
demo
    get     ${baidu_url}      # 进入百度首页
    FOR     ${i}    IN     @{search_words}
        clear   ${search_box}  # 清除搜索框
        send keys    ${i}   ${search_box}  # 搜索框输入搜索词
        click    ${search_button}  # 点击搜索按钮
    END
    sleep    3
    quit