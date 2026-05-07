from langchain.agents import Tool
from langchain_openai import ChatOpenAI
import subprocess
import tempfile
import os


class CodeGenerationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            # Replace with your API Key
            openai_api_key="ark-393c4598-78a4-48ba-85bd-5c102890ad1f-63ce5",
            # The base URL for model invocation
            openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
            # Replace with Model ID
            model_name="glm-4-7-251222",
        )

        # 定义工具
        self.tools = [
            Tool(
                name="GenerateCode",
                func=self._generate_code,
                description="生成Python代码"
            ),
            Tool(
                name="TestCode",
                func=self._test_code,
                description="测试代码是否可以运行"
            ),
            Tool(
                name="FixBug",
                func=self._fix_bug,
                description="修复代码中的bug"
            ),
        ]

    def _generate_code(self, requirement: str) -> str:
        """生成代码"""
        prompt = f"""
        请根据以下需求生成Python代码：

        需求：{requirement}

        要求：
        1. 代码要清晰、可读
        2. 添加必要的注释
        3. 包含错误处理
        4. 包含使用示例

        请输出完整的可运行代码。
        """

        response = self.llm.invoke(prompt)
        code = self._extract_code(response.content)
        return code

    def _test_code(self, code: str) -> dict:
        """测试代码"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # 运行代码
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "代码执行超时"
            }

        finally:
            os.unlink(temp_file)

    def _fix_bug(self, code: str, error: str) -> str:
        """修复bug"""
        prompt = f"""
        以下代码有错误：

        代码：
        ```python
        {code}
        ```

        错误信息：
        {error}

        请修复这个bug并返回完整的正确代码。
        """

        response = self.llm.invoke(prompt)
        fixed_code = self._extract_code(response.content)
        return fixed_code

    def _extract_code(self, text: str) -> str:
        """从回复中提取代码"""
        # 提取```python...```之间的内容
        import re
        pattern = r"```python\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            return match.group(1).strip()
        else:
            return text.strip()

    def generate(self, requirement: str, max_attempts=3):
        """完整的代码生成流程"""
        print(f"📝 需求：{requirement}\n")

        # 步骤1：生成代码
        print("1️⃣ 生成代码...")
        code = self._generate_code(requirement)
        print(f"生成的代码：\n{code}\n")

        # 步骤2：测试代码
        print("2️⃣ 测试代码...")

        for attempt in range(max_attempts):
            test_result = self._test_code(code)

            if test_result["success"]:
                print("✅ 测试通过！")
                print(f"输出：{test_result['output']}")

                # 步骤3：添加文档
                print("\n3️⃣ 添加文档...")
                documented_code = self._add_documentation(code)

                return documented_code

            else:
                print(f"❌ 测试失败（尝试{attempt + 1}/{max_attempts}）")
                print(f"错误：{test_result['error']}\n")

                # 修复bug
                print("🔧 修复bug...")
                code = self._fix_bug(code, test_result['error'])
                print(f"修复后的代码：\n{code}\n")

        # 所有尝试都失败
        return {
            "success": False,
            "message": f"经过{max_attempts}次尝试仍无法生成可运行的代码",
            "last_code": code,
        }

    def _add_documentation(self, code: str) -> str:
        """添加文档字符串"""
        prompt = f"""
        为以下代码添加详细的文档字符串（docstring）和使用说明：

        ```python
        {code}
        ```

        要求：
        1. 每个函数都有docstring
        2. 包含参数说明
        3. 包含返回值说明
        4. 包含使用示例
        """

        response = self.llm.invoke(prompt)
        return self._extract_code(response.content)


# 使用示例
agent = CodeGenerationAgent()

result = agent.generate("""
写一个函数，计算列表中所有数字的平方和。
要求：
- 输入是一个数字列表
- 返回平方和
- 包含错误处理（如果输入不是数字）
""")

print(result)

result = agent.generate("""
写一个函数，计算斐波那契数列。
""")

print(result)