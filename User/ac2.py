import sublime
import sublime_plugin
import os
import re
import LSP.plugin


class CssModulesAutocompleteCommand(sublime_plugin.TextCommand):
    css_classes_cache = {}

    def run(self, edit):
        # Получаем текущий вид и позицию курсора
        view = self.view
        locations = view.sel()

        if not locations:
            view.run_command("auto_complete")
            return

        location = locations[0].b

        # Проверяем, является ли текущий код jsx attrs
        # if not view.match_selector(location, "meta.jsx.js meta.tag.attributes.js"):
        #     print("non_in_tag_attrs")
        #     view.run_command("auto_complete")
        #     return

        # Получаем содержимое файла
        content = view.substr(sublime.Region(0, view.size()))

        # Ищем все импорты модулей
        imports = self.find_css_module_imports(content)

        # Проверяем, находится ли курсор после алиаса
        alias, strip_line, non_space_before_caret, is_inside_classnames = self.get_css_module_alias_context(
            view, location, imports
        )

        if not is_inside_classnames:
            view.run_command("auto_complete")
            return

        # Получаем путь к CSS файлу для текущего алиаса
        css_file_path = self.resolve_file_path(view, imports[alias])

        if not css_file_path:
            view.run_command("auto_complete")
            return

        # Получаем классы из файла
        css_classes = self.get_css_classes(css_file_path)

        # Формируем список автокомплитов
        completions = []
        for cls in css_classes:
            if "-" in cls:
                completion = (f'{alias}["{cls}"]\t{alias}.module.css', f'{alias}["{cls}"]')
            else:
                completion = (f"{alias}.{cls}\t{alias}.module.css", f'{alias}.{cls}')
            completions.append(completion)

        # Показываем пользовательское окно автокомплита
        view.show_popup_menu(
            [item[0] for item in completions],
            lambda index: self.insert_completion(index, completions, view, edit, location, alias, strip_line, non_space_before_caret)
        )

        # view.settings().set("css_module_completions", completions)

        # # Запускаем стандартный автокомплит
        # view.run_command("auto_complete
        # self.show_custom_popup(view, completions, location, edit, alias, strip_line, non_space_before_caret)

    # def show_custom_popup(self, view, completions, location, edit, alias, strip_line, non_space_before_caret):
    #     """Отображает кастомное всплывающее окно рядом с кареткой."""
    #     html = "<ul>"
    #     for i, item in enumerate(completions):
    #         html += f"<li id='{i}'>{item[0]}</li>"
    #     html += "</ul>"

    #     def on_hide():
    #         view.erase_regions("css_popup_highlight")

    #     # Показ всплывающего окна
    #     view.show_popup(
    #         html,
    #         location=-1,
    #         max_width=300,
    #         on_navigate=lambda index: self.insert_completion(
    #             int(index), completions, view, edit, location, alias, strip_line, non_space_before_caret
    #         ),
    #         on_hide=on_hide
    #     )

    def insert_completion(self, index, completions, view, edit, location, alias, strip_line, non_space_before_caret):
        """Вставляет выбранное автодополнение."""
        if index == -1:
            view.run_command("auto_complete")
            return  # Пользователь закрыл меню

        _, text = completions[index]
        alias_and_after_len = len(re.search(rf'{alias}.*$', non_space_before_caret).group())
        region_to_replace = sublime.Region(location, location - alias_and_after_len)
        # after_bracket_len = len(non_space_before_caret.split('{')[-1])

        # region_to_replace = sublime.Region(location, location - after_bracket_len)

        # view.erase(sublime.Edit(view.id()), region_to_replace)
        view.replace(edit, region_to_replace, text)
        # view.run_command("replace", {"edit": sublime.Edit(view.id()),"region": region_to_replace, "text": text})
        # view.run_command("insert", {"characters": text})

    def find_css_module_imports(self, content):
        """Находит импорты CSS/SCSS модулей в файле."""
        imports = {}
        pattern = re.compile(
            r'import\s+(\*\s+as\s+[\w\d_$]+|[\w\d_$]+)\s+from\s+[\'"](.+?\.module\.(css|scss))[\'"]'
        )
        for match in re.finditer(pattern, content):
            if bool(re.search(r'^\*\s+as.*', match.group(1))):
                alias = re.search(r'[\w\d_$]+$', match.group(1)).group()
                filepath = match.group(2)
            else:
                alias = match.group(1)
                filepath = match.group(2)
            imports[alias] = filepath
        return imports

    def get_css_module_alias_context(self, view, location, imports):
        # Проверяет, находится ли курсор внутри class|className={. после алиаса
        line = view.line(location)
        line_text = view.substr(line)
        line_position = location - line.a
        strip_line = line_text[:line_position].strip()

        # if not strip_line:
        #     print("empty strp")
        #     return self.on_empty_strip_line(location)

        if re.search(r'.*\s$', line_text[:line_position]) or not strip_line:
            print("space on end strip line or empty strip line")
            return None, None, None, False

        non_space_before_caret = strip_line.rsplit(maxsplit=1)[-1]

        for alias in imports.keys():
            alias_substrings = [alias[:i] for i in range(1, len(alias) + 1)]
            # Делал реакцию на куски алиаса но пока передумал.
            # classnames_pattern = rf"^(class|className)={{({'$|'.join(alias_substrings)})(\.|\[|\[\"|\[\')?$"
            classnames_pattern = rf"^(class|className|classList)={{?{{({alias})(\.|\[|\[\"|\[\')?$"
            # Попытка жпт
            # if non_space_before_caret.startswith(alias):

            if re.search(classnames_pattern, non_space_before_caret) or re.search(rf'\,?\[{alias}(\.|\[|\[\"|\[\')?', non_space_before_caret):
                return alias, strip_line, non_space_before_caret, True
        return None, None, None, False

    # def on_empty_strip_line(self, location):
    #     print("in on_empty_strip_line")
    #     # Получить номер строки и столбца для текущей позиции
    #     current_row, current_col = self.view.rowcol(location)

    #     # Получить предыдущую строку
    #     if current_row > 0:
    #         prev_line_start = self.view.text_point(current_row - 1, 0)
    #         prev_line_region = self.view.line(prev_line_start)
    #         prev_line_text = self.view.substr(prev_line_region)
    #     else:
    #         prev_line_text = None
    #     return None, None, None, False

    def resolve_file_path(self, view, filepath):
        """Преобразует относительный путь к файлу в абсолютный."""
        file_dir = os.path.dirname(view.file_name())
        abs_path = os.path.abspath(os.path.join(file_dir, filepath))
        return abs_path if os.path.isfile(abs_path) else None

    def get_css_classes(self, filepath):
        """Извлекает классы из CSS/SCSS файла."""
        # TODO: !! chache
        # if filepath in self.css_classes_cache:
            # return self.css_classes_cache[filepath]

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
