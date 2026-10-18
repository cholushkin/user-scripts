import os
import fnmatch

class PromptContextCollector:
    def __init__(self, directories=None, files=None, includes=None, ignores=None, template_path=None, template_vars=None, output_path="prompt_context.txt"):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",".."))
        
        print("🔧 Initializing PromptContextCollector...")
        
        if directories is None:
            self.directories = []
            print("   - directories omitted: defaulting to []")
        else:
            self.directories = directories

        if files is None:
            self.files = []
            print("   - files omitted: defaulting to []")
        else:
            self.files = files

        if includes is None:
            self.includes = ["*"]
            print("   - includes omitted: defaulting to ['*']")
        else:
            self.includes = includes

        if ignores is None:
            self.ignores = ["__pycache__/*", "*.pyc", ".git/*"]
            print("   - ignores omitted: defaulting to ['__pycache__/*', '*.pyc', '.git/*']")
        else:
            self.ignores = ignores

        if template_path is None:
            self.template_path = None
            print("   - template_path omitted: prompt template substitution will be skipped")
        else:
            self.template_path = os.path.join(self.project_root, template_path)

        if template_vars is None:
            self.template_vars = {}
            print("   - template_vars omitted: defaulting to {}")
        else:
            self.template_vars = template_vars

        if output_path == "prompt_context.txt":
            print(f"   - output_path omitted: defaulting to '{output_path}'")
        
        self.output_path = os.path.join(self.project_root, output_path)
        self.collected_files = []

    def _match_patterns(self, path, patterns):
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

    def _should_include(self, file_path):
        filename = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, self.project_root)
        if file_path in [os.path.join(self.project_root, f) for f in self.files]:
            return True
        return self._match_patterns(filename, self.includes) and not self._match_patterns(rel_path, self.ignores)

    def _resolve_paths(self):
        resolved = set()

        # Process directories
        for directory in self.directories:
            abs_directory = os.path.join(self.project_root, directory)
            if os.path.isdir(abs_directory):
                for root, _, files in os.walk(abs_directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._should_include(file_path):
                            resolved.add(file_path)

        # Add specific files
        for file in self.files:
            abs_file = os.path.join(self.project_root, file)
            if os.path.isfile(abs_file):
                resolved.add(abs_file)
            else:
                print(f"❌ file not found: {file}")

        return list(resolved)

    def _substitute_template(self):
        # Gracefully handle omitted template_path without raising FileNotFoundError
        if not self.template_path:
            return ""
        if not os.path.exists(self.template_path):
            print(f"⚠️ Template file not found: {self.template_path}. Skipping template substitution.")
            return ""
            
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()
        for key, value in self.template_vars.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
        
    def run(self):
        print(f"\n🛠 Starting PromptContextCollector Execution")
        print(f"📁 Project Root: {self.project_root}")
        print("-" * 50)

        resolved_paths = self._resolve_paths()

        collected = 0

        with open(self.output_path, 'w', encoding='utf-8') as out:

            out.write("// --- Source Blob ---\n\n")

            # --- Files Included Section ---
            out.write("Files included:\n")
            if not resolved_paths:
                out.write("- No files resolved with current parameters.\n")
            for path in resolved_paths:
                rel_path = os.path.relpath(path, self.project_root)
                out.write(f"- {rel_path}\n")

            out.write("\n" + "-" * 50 + "\n\n")

            # --- File Contents ---
            for path in resolved_paths:

                rel_path = os.path.relpath(path, self.project_root)

                try:
                    with open(path, "r", encoding="utf-8") as src:
                        out.write(f"// --- Start File: {rel_path} ---\n\n")
                        out.write(src.read())
                        out.write(f"\n\n// --- End File: {rel_path} ---\n\n")

                    self.collected_files.append(rel_path)

                    print(f"✅ Added: {rel_path}")

                    collected += 1

                except Exception as e:

                    print(f"❌ Error reading {rel_path}: {e}")

                    out.write(f"// !!! Error reading file {rel_path}: {e} !!!\n\n")

            # --- Prompt Section ---
            prompt_text = self._substitute_template()
            
            # Only append prompt section if a template was successfully generated
            if prompt_text.strip():
                out.write("\n" + "-" * 50 + "\n")
                out.write("// --- Prompt ---\n\n")
                out.write(prompt_text)

        print("-" * 50)
        print(f"🎯 Collection complete: {collected} file(s) added.")
        print(f"📝 Output written to: {self.output_path}")