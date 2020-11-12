# -*- coding: UTF-8 -*-

import shutil
import os
import sys
import json
sys.path.append("./lib/") 
from RepoScanner import RepoScanner
from MetaWebBlogClient import MetaWebBlogClient
from bs4 import BeautifulSoup
import datetime

orig_dir = "../public/"
repo_dir = "../public_cnblogs/"
ignore_files = ["../public/index.html"]
ignore_dirs = ["../public/page/", "../public/archives"]

header = ""

with open('./config/header.html', 'r', encoding='utf-8') as f:
    header = f.read()

# Formating the ignore configurations
for i in range(len(ignore_files)):
    ignore_files[i] = ignore_files[i].replace('\\', '/')
for i in range(len(ignore_dirs)):
    ignore_dirs[i] = ignore_dirs[i].replace('\\', '/')

# Scan the public dir containing the htmls

print('\033[44m\033[37m[INFO]\033[0m Process Started.')

if os.path.exists(repo_dir):
    for sub_dir in os.listdir(repo_dir):
        if os.path.isdir(os.path.join(repo_dir, sub_dir)) and sub_dir != '.git': 
            shutil.rmtree(os.path.join(repo_dir, sub_dir))
        if os.path.isfile(os.path.join(repo_dir, sub_dir)):
            os.remove(os.path.join(repo_dir, sub_dir))

index_files = []

# Filtering the files needed to post
for root, dirs, files in os.walk(orig_dir):
    for file in files:
        try:
            file_name = str(file)
            file_path = os.path.join(root, file)
            file_dir = root.replace('\\', '/')
            file_path = file_path.replace('\\', '/')
            
            flag = True
            
            for ignore_dir in ignore_dirs:
                if file_dir.startswith(ignore_dir):
                    flag = False
                    break
            for ignore_file in ignore_files:
                if file_path == ignore_file:
                    flag = False
                    break

            if (file_name == 'index.html' and flag):
                index_files.append(file_path)
                print('\033[42m\033[37m[LOGG]\033[0m File Detected:', file_path)
            
        except Exception as e:
            raise e

print('\033[44m\033[37m[INFO]\033[0m File Detection Ended.')

# Filter the articles that are to be synced

resource_dict = {}

for index_file in index_files:
    post_body = ""
    with open(index_file, 'r', encoding='utf-8') as f:
        html_doc = f.read()
        soup = BeautifulSoup(html_doc, "html.parser")
        check_msg = soup.select('span[id=cnblogs_sync_text]')
        if (len(check_msg) == 0): continue
        post_body_list = soup.select('div[class=post-body]')
        if (len(post_body_list) == 0): continue
        print('\033[42m\033[37m[LOGG]\033[0m Target Detected:', index_file)
        for child in soup.descendants:
            if (child.name == 'img'):
                if ('data-original' in child.attrs and 'src' in child.attrs):
                    child['src'] = 'https://hexo.gyrojeff.moe' + child['data-original']
                elif ('src' in child.attrs):
                    child['src'] = 'https://hexo.gyrojeff.moe' + child['src']
            if (child.name == 'a'):
                if ('href' in child.attrs):
                    if (str(child['href']).startswith('/') and not str(child['href']).startswith('//')):
                        child['href'] = 'https://hexo.gyrojeff.moe' + child['href']
        post_body = soup.select('div[class=post-body]')[0]
        math_blocks = post_body.select('script[type="math/tex; mode=display"]')
        for math_block in math_blocks:
            math_string = str(math_block).replace('<script type="math/tex; mode=display">', '<p>\n\n$$').replace('</script>', '\n$$\n\n</p>')
            math_block.replace_with(BeautifulSoup(math_string, 'html.parser'))
    save_dir = os.path.join(repo_dir, index_file[len(orig_dir):-len("index.html")])
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    copyright_div = str(soup.select('div[class=my_post_copyright]')[0])
    with open(save_dir + 'index.html', 'w', encoding='utf-8') as f:
        f.write(header + '\n' + copyright_div + '\n' + str(post_body))
    tags = soup.select('div[class=post-tags]')
    tags_text = []
    if len(tags) != 0:
        tags_div = tags[0].select('a')
        if len(tags_div) > 0:
            for tag in tags_div:
                tags_text.append(tag.contents[1][1:])
    
    resource_dict[save_dir + 'index.html'] = {
        'tags': tags_text, 
        'title': soup.select('meta[property="og:title"]')[0]['content']
    }
    print('\033[44m\033[37m[INFO]\033[0m File Generated:', save_dir + 'index.html')

print('\033[44m\033[37m[INFO]\033[0m File Generation Ended.')


# Scan changes

repoScanner = RepoScanner(repo_dir)
scanResult = repoScanner.scan()

print(scanResult)

# TODO: 增加div (html) ：本文已经发表在博客上，为了更好的阅读体验，请移步至博客

if not os.path.exists('./data/'):
    os.mkdir('./data/')


blog_data = {}

try:
    with open('./data/blog_data.json', 'r', encoding="utf-8") as f:
        blog_data = json.load(f)
except:
    print('\033[44m\033[37m[INFO]\033[0m Blog data file doesn\'t exist. Initializing.')
finally:
    f.close()

client = MetaWebBlogClient('./config/blog_config.json')
if not os.path.exists('./config/blog_config.json'):
    client.createConfig()
else: client.readConfig()

for git_path in scanResult['new']:
    try:
        file_path = os.path.join(repo_dir, git_path)
        resources = resource_dict[file_path]
        tag_string = ''
        for tag in resources['tags']:
            tag_string = tag_string + tag + ';'
        source_string = ''
        with open(file_path, 'r', encoding='utf-8') as f:
            source_string = f.read()
        postid = client.newPost({
            "title": resources['title'],
            "description": source_string,
            "mt_keywords": tag_string[:-1]
        }, True)
        print('\033[42m\033[37m[LOGG]\033[0m 发布随笔:', resources['title'], postid, tag_string[:-1])
        repoScanner._repo.index.add(git_path)
        repoScanner._repo.index.commit('New Post: id(' + postid + ')')
        blog_data[file_path] = postid
        with open('./data/blog_data.json', 'w', encoding="utf-8") as f:
            json.dump(blog_data, f)
    except Exception as e:
        print('发布失败:', file_path)
        print('错误:')
        print(str(e))

for git_path in scanResult['changed']:
    try:
        file_path = os.path.join(repo_dir, git_path)
        resources = resource_dict[file_path]
        tag_string = ''
        for tag in resources['tags']:
            tag_string = tag_string + tag + ';'
        source_string = ''
        with open(file_path, 'r', encoding='utf-8') as f:
            source_string = f.read()
        client.editPost(str(blog_data[file_path]), {
            "title": resources['title'],
            "description": source_string,
            "mt_keywords": tag_string[:-1]
        }, True)
        print('\033[42m\033[37m[LOGG]\033[0m 修改随笔:', resources['title'], blog_data[file_path], tag_string[:-1])
        repoScanner._repo.index.add(git_path)
        repoScanner._repo.index.commit('Modify Post: id(' + blog_data[file_path] + ')')
    except Exception as e:
        print('修改失败:', file_path)
        print('错误:')
        print(str(e))

for git_path in scanResult['deleted']:
    try:
        file_path = os.path.join(repo_dir, git_path)
        client.deletePost(str(blog_data[file_path]), False)
        print('\033[42m\033[37m[LOGG]\033[0m 删除随笔:', git_path, blog_data[file_path])
        repoScanner._repo.index.remove(git_path)
        repoScanner._repo.index.commit('Delete Post: id(' + blog_data[file_path] + ')')
        blog_data[file_path] = ''
        with open('./data/blog_data.json', 'w', encoding="utf-8") as f:
            json.dump(blog_data, f)
    except Exception as e:
        print('删除失败:', file_path)
        print('错误:')
        print(str(e))

with open('./data/blog_data.json', 'w', encoding="utf-8") as f:
    json.dump(blog_data, f)

# Configuration syncing

with open('../config_cnblogs/blog_data.json', 'w', encoding="utf-8") as f:
    json.dump(blog_data, f)
config_file_data = None
with open('./config/blog_config.json', 'r', encoding='utf-8') as f:
    config_file_data = json.load(f)
with open('../config_cnblogs/blog_config.json', 'w', encoding="utf-8") as f:
    json.dump(config_file_data, f)