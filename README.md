![img](seliky/seliky.jpg)

### seliky-史上最佳UI自动化测试库

seliky致力于做好UI自动化及爬虫中的与页面交互的逻辑，在原生selenium和drissionpage的基础上做了完美的封装，可以是helium等ui封装库的平替，它的主要特性如下：

------
1. **极致简约稳定，学习简单**🔥🔥🔥🔥🔥
   - 作者把大量复杂、冗余的操作进行了完美的封装，写代码时调用的语句非常简约干净。
   - 大量降低了学习成本，使用者无需了解selinium内在机制，甚至无需掌握python。
2. **平滑替代**🔥🔥🔥🔥🔥
   - 内部平滑代替：提供了基于selenium的seliky，和基于drissionpage的seliky_dri，api相同，相互之间可以无痛平滑代替。
   - 整库平滑代替：提供的公用api涵盖其它主流封装库的90%，方便公司将其它库平滑迁移至seliky。
   - 注：截止2025，我仍认为selinium和drissionpage是两个最佳的ui交互库，所以才有上述的封装。
3. **交互稳定**🔥🔥🔥🔥🔥
   - 原生selenium最大的弊病就是不稳定找不到元素，明明元素就在页面。seliky的交互机制通过最大耗时计算巧妙又精确的解决了元素就在页面但找不到的问题。
   - 多重机制保障稳定性。核心方法如 click-点击、send_keys-输入值都使用多套机制，所以才稳定好用。
4. **统一采用xpath定位**🔥🔥🔥
   - 不同的定位符的管理一直是业内通病，为方便管理，seliky统一采用xpath定位。
   - 这个大胆的设计源于吾先后在多家大厂调研得已验证，做ui自动化掌握好xpath这种万能定位足够了。
5. **元素高亮**🔥🔥🔥
   - 元素在交互时默认高亮闪烁，这一特效方便在执行时观察页面。
   - 在无界面时默认关闭。
6. **无侵入式封装**🔥🔥
   - 有很多优秀的封装库，把selinium的原生方法干没了，这是多大的自信。
   - seliky是在selinium的基础之上做的封装，丝毫不影响交互中使用原生方法，有利于熟悉了原生的用户无缝切换过来。
7. **新版优势**🔥
   - 有很多优秀的封装库是基于selenium3甚至selenium2来封装的，导致最新版的特性没体现出来。seliky基于selenium4来做的，具有新版新特性的优势。
   - 自动下载driver，seliky在早期（2022年）就已经支持自动下载driver，当时原生的是不支持的，可见吾敏锐的前瞻意识。后来selenium4支持了自动下载driver，吾也就进行了融合。
8. **GRID分布式化繁为简**🔥🔥🔥🔥🔥
   - grid分布式搭建一直是复杂而琐碎的，而且有很多公司并不需要做ui自动化的兼容性，这一块很多自动化人员也不太重视。即便如此，吾还是进行了整合，只需要准备好jar包即可，通过remote_location参数实现了从机的控制。一大堆的配置变成了一个参数，实现了grid分布式化繁为简。
9. **兼容robotframework框架**🔥🔥
   - 还有公司使用RF框架的，可以使用seliky作为rf的平替。
10. **自动化、爬虫通用**🔥🔥🔥
    - 被反反爬的认证机制搞怕了？？试试seliky的seliky_dri，无需driver，去掉了繁琐的对抗过程。
11. **自动提取注释**🔥🔥
    - 支持自动从xpath中提取关键词，来作为报告里的说明
12. **简化xpath写法、精准计算timeout、click多重保障等强悍逻辑、一切为了稳定**🔥🔥🔥🔥🔥

更多其它好用的特性，尽在seliky，使用 pip install seliky 来体验吧...

------



### 一个案例告诉你有多简单

案例：访问百度，依次搜索3组关键词，依次校验结果，结果正确的话随便打印些东西。

分析：你只需要记住几个关键的方法即可，请求-get、点击-click、输入-send_keys、是否可见-is_visible，代码示例如下：

```python
from seliky.seliky import WebDriver

# 实例化
page = WebDriver(executable_path=r'c:\chromedriver.exe')

# 打开浏览器
page.open_browser()

# 请求某度
page.get("https://www.baidu.com")

# 依次搜索关键词
search_words = ["小张", "小李", "小刘"]
for i in search_words:
    page.send_keys('//input[@id="kw"]', i)  # 输入值
    page.click('//input[@id="su"]')  # 点击搜索
    if page.is_visible('//img[@class="index-logo-src"]'):  # 判断是否出现logo
        print('百度logo已正确加载')

```

如果你是做爬虫的，或者想寻求无driver的方式来与页面交互，可以试试seliky_dri：

```python
from seliky.seliky_dri import WebDriver


def ui():
    # 实例化无需传参，有谷歌浏览器即可
    page = WebDriver()

    # 打开浏览器
    page.open_browser()

    # 去某个网站
    page.get('https://sahitest.com/demo')

    # 点击某个按钮，复制按钮上面的文字来的
    page.click('Link Test', bac_sleep=3)

    # 同上
    page.get('https://sahitest.com/demo')
    page.click('Form Test', bac_sleep=3)
    page.get('https://sahitest.com/demo')
    page.click('Label Page', bac_sleep=3)


if __name__ == '__main__':
    ui()

```

