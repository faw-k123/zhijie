# 智解国音一键启动包

## 首次使用

1. 确认已安装 Python 3.11、Node.js 22 或更高版本。
2. 右键 `install.ps1`，选择“使用 PowerShell 运行”，或在 PowerShell 中执行：

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\install.ps1
   ```

3. 安装成功后，按需编辑 `app\backend\.env`，填写 SQL Server、Neo4j 和外部 AI 服务配置。
4. 双击 `start.bat`。脚本会等待前端可访问后再自动打开登录页，最长等待 90 秒。

如果安装过程中出现错误，脚本会停止并显示具体错误，不会误报“安装完成”。

## 访问地址

- 前端：http://127.0.0.1:5175/login
- 后端：http://127.0.0.1:8000

SQL Server 和 Neo4j 仍需单独安装并运行；本启动包只负责项目本身及 Python/Node 依赖。
