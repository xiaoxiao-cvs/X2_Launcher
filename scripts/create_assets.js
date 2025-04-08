const fs = require('fs');
const path = require('path');

// 创建assets目录
const assetsDir = path.join(__dirname, '../assets');
if (!fs.existsSync(assetsDir)) {
    fs.mkdirSync(assetsDir, { recursive: true });
    console.log('创建assets目录成功');
}

// 创建一个简单的占位图标文件
// 注意：这只是一个占位符，真正的图标需要用图标编辑器创建
const iconPath = path.join(assetsDir, 'app.ico');
if (!fs.existsSync(iconPath)) {
    console.log('需要添加app.ico文件到assets目录');
    console.log(`请将一个有效的.ico文件放到: ${iconPath}`);
}

// 添加默认图片作为备用
const defaultPngPath = path.join(assetsDir, 'default.png');
if (!fs.existsSync(defaultPngPath)) {
    // 创建一个1x1像素的PNG文件作为占位符
    const emptyPngBuffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
    fs.writeFileSync(defaultPngPath, emptyPngBuffer);
    console.log('创建默认图片成功');
}

console.log('资源初始化完成');
