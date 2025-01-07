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

        # Проверяем, является ли текущий код jsx
        if not view.match_selector(
            locations[0], "meta.jsx.js meta.tag.attributes.js"
        ):
            return None

        # Получаем содержимое файла
        content = view.substr(sublime.Region(0, view.size()))

        # Ищем все импорты модулей
        imports = self.find_css_module_imports(content)

        # Проверяем, находится ли курсор после алиаса
        # внутри определения classNames
        alias, strip_line, is_inside_classnames = self.get_css_module_alias_context(
            view, locations[0], imports)
        if not is_inside_classnames:
            return None

        num_prop_accessor_symbols = len(strip_line) - re.search(alias, strip_line).span()[1]

        # Удаляем текст перед алиасом
        # line_region = view.line(locations[0])
        # line_text = view.substr(line_region)
        # alias_index = line_text.find(alias)

        # if alias_index != -1:
        #     # Удаляем всё перед алиасом
        #     region_to_erase = sublime.Region(line_region.a, line_region.a + alias_index)
        #     view.run_command("erase_region", {"region": (region_to_erase.a, region_to_erase.b)})


        region_to_erase = sublime.Region(
            locations[0] - len(alias) - num_prop_accessor_symbols,
            locations[0]
        )

        completions = []

        # Для определённого алиаса импорта подтягиваем классы
        # for alias, filepath in imports.items():
        # Абсолютный путь к файлу
        css_file_path = self.resolve_file_path(view, imports[alias])

        if not css_file_path:
            return None

        # Получаем классы из SCSS/CSS
        css_classes = self.get_css_classes(css_file_path)

        # sublime.Region(locations[0] - len(alias) - num_prop_accessor_symbols, locations[0])
        # Формируем автокомплиты
        for cls in css_classes:
            if "-" in cls:
                completion = (f'"{cls}"\tCSS Module', f'["{cls}"]')
            else:
                completion = (f"{cls}\tCSS Module", cls)
            completions.append(completion)

        # Получаем текущие автокомплиты от Sublime
        # existing_completions = view.extract_completions(prefix)

        # Формируем итоговый список автокомплитов
        # combined_completions = completions + \
            # [(item, item) for item in existing_completions]

        # Указываем флаг KEEP_PREFIX, чтобы сохранить префикс
        # return combined_completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
        return completions

    def find_css_module_imports(self, content):
        """
        Находит импорты CSS/SCSS модулей в файле.
        Пример: import styles from './file.module.scss';
        """
        imports = {}
        # Регулярное выражение для поиска импортов
        pattern = re.compile(r'import\s+(\*\s+as\s+[\w\d_$]+|[\w\d_$]+)\s+from\s+[\'"](.+?\.module\.(css|scss))[\'"]')
        for match in re.finditer(pattern, content):

            if bool(re.search(r'^\*\s+as.*', match.group(1))):
                # Импорт с "* as"
                alias = re.search(r'[\w\d_$]+$', match.group(1)).group()
                filepath = match.group(2)
            else:
                # Импорт без "* as"
                alias = match.group(1)
                filepath = match.group(2)
            # Далее можно обрабатывать alias и filepath
            imports[alias] = filepath
        return imports

    def get_css_module_alias_context(self, view, location, imports):
        # Проверяет, находится ли курсор внутри определения class|classNames,
        # получаем конкретный алиас, если есть в строке

        # Получаем строку, в которой находится каретка
        line = view.line(location)
        line_text = view.substr(line)
        line_position = location - line.a
        strip_line = line_text[:line_position].strip()

        if not strip_line:
            return None, False
        non_space_before_caret = strip_line.rsplit(maxsplit=1)[-1]

        for alias in imports.keys():
            alias_substrings = [alias[:i] for i in range(1, len(alias) + 1)]
            classnames_pattern = rf"^(class|className)={{({'$|'.join(alias_substrings)})(\.|\[|\[\"|\[\')?$"

            if re.search(classnames_pattern, non_space_before_caret):
                return alias, strip_line, True
        return None, None, False

    def resolve_file_path(self, view, filepath):
        """
        Преобразует относительный путь к файлу в абсолютный.
        """
        file_dir = os.path.dirname(view.file_name())
        abs_path = os.path.abspath(os.path.join(file_dir, filepath))
        return abs_path if os.path.isfile(abs_path) else None

    def get_css_classes(self, filepath):
        # Извлекает классы из CSS/SCSS файла.

        if filepath in self.css_classes_cache:
            return self.css_classes_cache[filepath]

        # Читаем файл и ищем классы
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                classes = re.findall(r'^\s*\.([\w\d_-]+)', content, re.MULTILINE)
                self.css_classes_cache[filepath] = classes
                return classes
        except Exception as e:
            print(f"Ошибка при чтении файла {filepath}: {e}")
            return []

    @classmethod
    def clear_cache(cls):
        """Очищает кэш классов."""
        cls.css_classes_cache = {}
