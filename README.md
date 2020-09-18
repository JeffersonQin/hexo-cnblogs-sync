# hexo-cnblogs-sync

## Introduction

这是一个同步Hexo博客和博客园的脚本，使用GitPython做版本控制，MetaWeblog发布文章。整个流程还是基于Hexo Generator的HTML文件。

## 配置

Clone本项目到Hexo博客目录下就行，添加为`submodule`，此外，请在`themes/next/layout/_macro/post.swig`中，选择合适的地方加入：

```swig
{% if post.cnblogs %}
    <br>
    <span class="post-meta-item">
        <span class="post-meta-item-icon">
            <i class="fas fa-rss"></i>
        </span>
    <span class="post-meta-item-text" id="cnblogs_sync_text"><a href="https://www.cnblogs.com/jeffersonqin/">博客园</a> 同步已开启</span>
    </span>
{% endif %}
```
## Notice

如果发现中文转码出现问题，记得运行下面这行命令：
```bash
git config --global core.quotepath false
```
