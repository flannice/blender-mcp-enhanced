@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================
echo 正在下载 Blender 4.2 LTS 稳定版
echo ======================================
curl -L "https://download.blender.org/release/Blender4.2/blender-4.2.0-windows-x64.zip" -o blender.zip

echo.
echo 正在解压到指定路径...
mkdir "E:\Chat\Trae-CN-IDE\Claude+Blender" 2>nul
tar -xf blender.zip -C "E:\Chat\Trae-CN-IDE\Claude+Blender" --strip-components 1

echo.
echo Blender 安装完成！
del blender.zip
echo 按任意键退出
pause >nul