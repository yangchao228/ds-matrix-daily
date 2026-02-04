# GitHub 推送说明

要完成项目推送，请按以下步骤操作：

## 1. 添加SSH公钥到GitHub账户
- 登录GitHub账户
- 前往 Settings > SSH and GPG keys
- 点击 "New SSH key"
- Title: "OpenClaw DS-Matrix-Daily"
- Key: 将以下内容复制粘贴进去

```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCyDxHj8D+Y4N9xd0qE2LZDiAjU1s2Zmjtge4inoCKC8Ttw1B0myRglTSvq4NgerXxImcghcnccDfk/tnDrlNjiae1r/BzjMfXQDX5Gg5os4NM26PX/H0s1tGVW6/PnHoP8v8teVDml1klTqhPCtZz1SiTOrYf/U4W9FFK43Po9pe7GkSF3gwLchzSZB7BccF/RbpY8gKZhI1yWAyKeZSMhgK2YXqtgaZHOT43HLmNmopXeb/PwcPdbwz/99FjUKbyo+sEWVF1SFhfZLl5T84hFmJOaTho98ZR77GFTXMt3+Z1K4iqi+rfblv0vV4ycU8j9SEucRDn58WM3PLxEgtjwgxYENhvSlkTa+SoAKQeDv+0TGoOavkB7aRTJXFuJpBy0O7XkwZwnFLUxaZZWbRaIOF2Snw94AIULF66crMikrTjTymR1NKCoeu1acMFnjUcMfuquaA/RzRRHiw5NIiXFXoz7gLFMlN1tjbPiiGtp6pqc5xd/ShCrQ5DDd0RqeiHTPASvM2f1cC+c8TK0aKCMiqmq4wHniWrOlzrHZp71y+Bd/WKl5M0ok9I1BlTn2fP7NfItT/IlToiu8pJiz4+PHtdJB0DIsmF3TfZsZIP11mzon1/emvwPpsBr1QiaFIJY5rSlxmi43gehmRDnML4Pix0ipVPYmMjDKENa7Sk0hQ== yangchao228@example.com
```

## 2. 验证SSH连接
完成后，返回终端并运行：
```
ssh -T git@github.com
```

你应该会看到类似 "Hi username! You've successfully authenticated..." 的消息。

## 3. 推送代码
验证成功后，运行：
```
cd ds-matrix-daily && git push -u origin main
```

这样你的代码就会成功推送到GitHub仓库了。
