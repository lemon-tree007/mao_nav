#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 mock_data.js 中所有 HTTP 图标到 public/sitelogo 目录
"""

import os
import re
import json
import requests
import time
from urllib.parse import urlparse
from pathlib import Path
import sys

def extract_mock_data():
    """从 mock_data.js 文件中提取数据"""
    mock_file = "src/mock/mock_data.js"
    
    if not os.path.exists(mock_file):
        print(f"❌ 找不到文件: {mock_file}")
        return None
    
    with open(mock_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式提取 JSON 数据
    match = re.search(r'export const mockData = ({.*})', content, re.DOTALL)
    if not match:
        print("❌ 无法解析 mock_data.js 文件")
        return None
    
    try:
        # 解析 JSON 数据
        data_str = match.group(1)
        data = json.loads(data_str)
        return data
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        return None

def get_all_http_icons(data):
    """获取所有 HTTP 地址的图标"""
    http_icons = []
    
    for category in data.get('categories', []):
        for site in category.get('sites', []):
            icon_url = site.get('icon', '')
            if icon_url.startswith('http'):
                # 提取域名作为文件名
                if 'favicon/' in icon_url:
                    # 从 icon.maodeyu.fun/favicon/domain 提取域名
                    domain = icon_url.split('/favicon/')[-1]
                else:
                    # 从普通URL提取域名
                    parsed = urlparse(site.get('url', ''))
                    domain = parsed.netloc
                
                http_icons.append({
                    'url': icon_url,
                    'domain': domain,
                    'filename': f"{domain}.ico",
                    'site_name': site.get('name', ''),
                    'site_url': site.get('url', '')
                })
    
    return http_icons

def download_icon(icon_info, output_dir, session):
    """下载单个图标"""
    url = icon_info['url']
    filename = icon_info['filename']
    filepath = output_dir / filename
    
    # 如果文件已存在，跳过
    if filepath.exists():
        print(f"⏭️  跳过已存在的文件: {filename}")
        return True
    
    try:
        print(f"📥 下载: {icon_info['site_name']} ({filename})")
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 检查文件大小
        if len(response.content) < 100:
            print(f"⚠️  文件过小，可能无效: {filename} ({len(response.content)} bytes)")
            return False
        
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 下载成功: {filename} ({len(response.content)} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败: {filename} - {e}")
        return False
    except Exception as e:
        print(f"❌ 保存失败: {filename} - {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始下载图标...")
    
    # 创建输出目录
    output_dir = Path("public/sitelogo")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录: {output_dir.absolute()}")
    
    # 提取数据
    print("📖 读取 mock_data.js...")
    data = extract_mock_data()
    if not data:
        return
    
    # 获取所有HTTP图标
    http_icons = get_all_http_icons(data)
    print(f"🔍 找到 {len(http_icons)} 个 HTTP 图标")
    
    if not http_icons:
        print("✅ 没有需要下载的图标")
        return
    
    # 创建会话以复用连接
    session = requests.Session()
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
    
    # 下载图标
    success_count = 0
    failed_count = 0
    
    print(f"\n📦 开始下载 {len(http_icons)} 个图标...\n")
    
    for i, icon_info in enumerate(http_icons, 1):
        print(f"[{i}/{len(http_icons)}] ", end="")
        
        if download_icon(icon_info, output_dir, session):
            success_count += 1
        else:
            failed_count += 1
        
        # 添加延迟避免请求过快
        time.sleep(0.5)
    
    # 关闭会话
    session.close()
    
    # 输出结果
    print(f"\n📊 下载完成!")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"📁 文件保存在: {output_dir.absolute()}")
    
    # 显示已下载的文件
    downloaded_files = list(output_dir.glob("*.ico"))
    if downloaded_files:
        print(f"\n📋 已下载的文件 ({len(downloaded_files)} 个):")
        for file in sorted(downloaded_files):
            size = file.stat().st_size
            print(f"  - {file.name} ({size} bytes)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        sys.exit(1)
