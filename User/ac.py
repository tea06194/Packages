import sublime
import sublime_plugin
import os
import re


class CssModulesAutocomplete(sublime_plugin.EventListener):
    # Словарь для кэширования классов из SCSS/CSS файлов
    css_classes_cache = {}

    def on_query_completions(self, view, prefix, locations):
        # Если prefix пустой, извлекаем текст перед курсором вручную
        if not prefix:
            word_region = view.word(locations[0] - 1)
            prefix = view.substr(word_region).strip()
        print("on_query_completions", prefix)
        # Проверяем, является ли текущий файл JS/TS/JSX/TSX (React)
        if not view.match_selector(locations[0], "source.js | source.ts | source.jsx | source.tsx"):
            return None
        print("in jsx|tsx")
        # Получаем содержимое файла
        content = view.substr(sublime.Region(0, view.size()))

        # Ищем все импорты модулей
        imports = self.find_css_module_imports(content)

        # Проверяем, находится ли курсор после алиаса внутри определения classNames
        alias, is_inside_classnames = self.get_css_module_alias_context(view, locations[0], imports)
        if not is_inside_classnames:
            return None

        completions = []
        print("imports: ", imports)
        # Для каждого найденного импорта подтягиваем классы
        for alias, filepath in imports.items():
            # Абсолютный путь к файлу
            css_file_path = self.resolve_file_path(view, filepath)
            if not css_file_path:
                continue

            # Получаем классы из SCSS/CSS
            css_classes = self.get_css_classes(css_file_path)

             # Формируем автокомплиты
             # Формируем автокомплиты
            for cls in css_classes:
                if "-" in cls:
                    completion = (f'"{cls}"\tCSS Module', f'["{cls}"]')
                else:
                    completion = (f"{cls}\tCSS Module", cls)
                completions.append(completion)

        # Получаем текущие автокомплиты от Sublime
        existing_completions = view.extract_completions(prefix)
        print(existing_completions)

        # Формируем итоговый список автокомплитов
        combined_completions = completions + [(item, item) for item in existing_completions]

        # Указываем флаг KEEP_PREFIX, чтобы сохранить префикс
        return combined_completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

    def find_css_module_imports(self, content):
        """
        Находит импорты CSS/SCSS модулей в файле.
        Пример: import styles from './file.module.scss';
        """
        imports = {}
        # Регулярное выражение для поиска импортов
        print("find_css_module_imports")
        pattern = re.compile(r'import\s+(\*\s+as\s+([\w\d_$]+)|[\w\d_$]+)\s+from\s+[\'"](.+\.module\.(?:css|scss))[\'"]')
        for match in re.finditer(pattern, content):
            print(match.groups())
            if len(match.groups()) == 3:
                # Импорт с "* as"
                alias = match.group(2)
                filepath = match.group(3)
            else:
                # Импорт без "* as"
                alias = match.group(1)
                filepath = match.group(2)
            # Далее можно обрабатывать alias и filepath
            imports[alias] = filepath
            print("for match in re.finditer")
        return imports

    def get_css_module_alias_context(self, view, location, imports):
        """Проверяет, находится ли курсор после алиаса внутри определения classNames"""
        # Получаем строку, в которой находится каретка
        row, col = view.rowcol(location)
        line = view.line(location)
        line_text = view.substr(line)
        # Ищем определения импортов CSS модулей в полученных импортах
        for alias, filepath in imports.items():
            print("get_css_module_alias_context","'", alias,"'")
            classnames_pattern = re.compile(r'className\s*=\s*{\s*(`\${)?')
            print(classnames_pattern, line_text)
            if re.search(classnames_pattern, line_text):
                print('true')
                return alias, True

        return None, False

    def resolve_file_path(self, view, filepath):
        """
        Преобразует относительный путь к файлу в абсолютный.
        """
        file_dir = os.path.dirname(view.file_name())
        abs_path = os.path.abspath(os.path.join(file_dir, filepath))
        return abs_path if os.path.isfile(abs_path) else None

    def get_css_classes(self, filepath):
        """
        Извлекает классы из CSS/SCSS файла.
        """
        if filepath in self.css_classes_cache:
            return self.css_classes_cache[filepath]

        # Читаем файл и ищем классы
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                classes = re.findall(r'\.([\w\d_-]+)', content)
                self.css_classes_cache[filepath] = classes
                return classes
        except Exception as e:
            print(f"Ошибка при чтении файла {filepath}: {e}")
            return []

    @classmethod
    def clear_cache(cls):
        """Очищает кэш классов."""
        cls.css_classes_cache = {}
        print("CSS Modules Cache Cleared")