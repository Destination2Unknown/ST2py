from flask import Flask, render_template, request, jsonify
import re


class ConvertorApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/convert", "convert", self.convert, methods=["POST"])

    def index(self):
        return render_template("index.html")

    def convert(self):
        st_code = request.json.get("st_code", "")
        if not st_code:
            return jsonify({"error": "Empty input"}), 400

        converted_code = self.convert_st_to_python(st_code)
        return jsonify({"converted_code": converted_code})

    def convert_st_to_python(self, st_code):
        variables = {}
        var_declaration_pattern = r"VAR(.*?)END_VAR"
        var_declaration_match = re.search(var_declaration_pattern, st_code, re.DOTALL)

        if var_declaration_match:
            var_declarations = var_declaration_match.group(1)
            var_lines = var_declarations.strip().split("\n")

            for line in var_lines:
                line = line.strip()
                if line:
                    split_line = line.split(":=", maxsplit=1)
                    if len(split_line) > 1:
                        var_declaration, var_value = split_line
                        var_name = var_declaration.split(":", maxsplit=1)[0].strip()
                        variables[var_name] = var_value.strip()
                    else:
                        var_declaration = split_line[0]
                        var_name = var_declaration.split(":", maxsplit=1)[0].strip()
                        variables[var_name] = None

        new_st_code = ""
        for var_name, var_value in variables.items():
            new_st_code += f"{var_name} = {var_value}\n"

        ret_code = re.sub(var_declaration_pattern, new_st_code, st_code, flags=re.DOTALL)
        ret_code = self.convert_ifs(ret_code)
        ret_code = self.convert_loops(ret_code)
        ret_code = self.convert_cases(ret_code)
        ret_code = self.clean_up_python_code(ret_code)

        return ret_code

    def convert_ifs(self, st_code):
        st_code = re.sub(r"ELSIF\s+(.*?)\s+THEN", r"elif \1:", st_code, flags=re.IGNORECASE)
        st_code = re.sub(r"ELSEIF\s+(.*?)\s+THEN", r"elif \1:", st_code, flags=re.IGNORECASE)
        st_code = re.sub(r"IF\s+(.*?)\s+THEN", r"if \1:", st_code, flags=re.IGNORECASE)
        st_code = re.sub(r"ELSE", r"else:", st_code, flags=re.IGNORECASE)
        st_code = re.sub(r"END_IF", r"", st_code, flags=re.IGNORECASE)
        return st_code

    def convert_loops(self, st_code):
        # Convert FOR loops
        for_loop_pattern = r"FOR\s+(.*?)\s*:=\s*(.*?)\s+TO\s+(.*?)\s+DO\s+(.*?)\s+END_FOR"
        st_code = re.sub(for_loop_pattern, r"for \1 in range(\2, \3 + 1):\n    \4\n", st_code, flags=re.DOTALL)

        # Convert WHILE loops
        st_code = re.sub(r"WHILE\s+(.*?)\s+DO", r"while \1:", st_code, flags=re.IGNORECASE)
        st_code = re.sub(r"END_WHILE", r"", st_code, flags=re.IGNORECASE)

        # Convert REPEAT loops
        repeat_loop_pattern = r"REPEAT\s*\n(.*?)\n\s*UNTIL\s+(.*?)\s+END_REPEAT"
        st_code = re.sub(repeat_loop_pattern, r"while not (\2):\n\1\n", st_code, flags=re.DOTALL)

        return st_code

    def convert_cases(self, st_code):
        case_pattern = r"(CASE\s+(.*?)\s+OF(.*?)END_CASE;)"
        cases = re.finditer(case_pattern, st_code, re.IGNORECASE | re.DOTALL)
        # Check each CASE pattern
        for singular_pattern in cases:
            case_check = singular_pattern.group(2).strip()
            case_block = singular_pattern.group(3).strip()

            python_code = f"match {case_check}:\n"

            case_blocks = re.finditer(r"(.*?):\s*((?:(?:(?<!:=):|[^:])*?))(?=\s*(?:\d+\s*:\s*|ELSE|END_CASE|$))", case_block, re.IGNORECASE | re.DOTALL)

            # Check each condition of CASE
            for case_match in case_blocks:
                condition = case_match.group(1).strip()
                code = case_match.group(2).strip()
                code = code.replace(":", "").replace(";", "")
                python_code += f"    case {condition}:\n"
                for line in code.split("\n"):
                    python_code += f"        {line.strip()}\n"

            # Check for ELSE pattern
            python_code = re.sub(r"ELSE", "_", python_code, flags=re.IGNORECASE)
            st_code = st_code.replace(singular_pattern.group(0), python_code)

        return st_code

    def clean_up_python_code(self, python_code):
        # Replace ST keywords with Python keywords...
        python_code = python_code.replace("RETURN", "return")
        python_code = python_code.replace("EXIT", "break")
        python_code = python_code.replace("ELSIF", "elif")
        python_code = python_code.replace("ELSEIF", "elif")
        python_code = python_code.replace("false", "False")
        python_code = python_code.replace("true", "True")
        python_code = python_code.replace(":=", "=")
        python_code = python_code.replace(";", "")
        python_code = python_code.strip()

        # Add newline at the end if not present
        if not python_code.endswith("\n"):
            python_code += "\n"

        # Replace duplicate empty lines
        python_code = re.sub(r"\n\s*\n{2,}", "\n\n", python_code)

        return python_code


if __name__ == "__main__":
    convertor = ConvertorApp()
    convertor.app.run("0.0.0.0", 5000)
else:
    gunicorn_app = ConvertorApp().app
