
alias subl='/c/Program\ Files/Sublime\ Text/sublime_text.exe'
alias graph='git log --all --decorate --oneline --graph'

# Убедитесь, что история включена
HISTFILE=~/.bash_history
HISTSIZE=1000
HISTFILESIZE=2000
HISTCONTROL=ignorespace:erasedups # Не пишем в историю команды с пробелом в начале и дубликаты
shopt -s histappend  # Добавление в историю, а не перезапись

# Настройка автодополнения по истории
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# Сохранять историю в файл при закрытии сессии
PROMPT_COMMAND="history -a; history -n; $PROMPT_COMMAND"



# history cleanup err cmds

# Если в Bash настроены переменные HISTCONTROL (например, ignorespace) или HISTIGNORE,
# они могут исключать определённые команды из сохранения в истории.
# Это приводит к тому, что номер последней команды в истории может быть неправильным.
# Чтобы избежать этой проблемы, используется улучшенная версия:

# debug_handler() {
#     LAST_COMMAND=$BASH_COMMAND
# }

# Для сохранения команд, завершившихся с ошибкой, используется обработчик ошибок error_handler,
# который срабатывает всякий раз, когда команда завершилась с ненулевым кодом возврата (ошибка).
# Это достигается с помощью команды trap.

# error_handler() {
#     local LAST_HISTORY_ENTRY=$(history | tail -1l)

#     if [ "$LAST_COMMAND" == "$(cut -d ' ' -f 2- <<< $LAST_HISTORY_ENTRY)" ]; then
#         FAILED_COMMANDS="$(cut -d ' ' -f 1 <<< $LAST_HISTORY_ENTRY) $FAILED_COMMANDS"
#     fi
# }

# Когда пользователь завершает сеанс Bash, команды,
# которые завершились с ошибкой, удаляются из истории.
# Это делается с помощью обработчика exit_handler, который срабатывает при выходе:
# Вместо использования uniq можно сразу сортировать и удалять дубликаты в FAILED_COMMANDS:
# Перед удалением можно добавить проверку, чтобы не пытаться удалять команды, если FAILED_COMMANDS пуст:

# exit_handler() {
#     if [ -n "$FAILED_COMMANDS" ]; then
#         for i in $(echo $FAILED_COMMANDS | tr ' ' '\n' | sort -rn | uniq);
#         do
#             history -d $i
#         done
#     fi

    # for i in $(echo $FAILED_COMMANDS | tr ' ' '\n' | uniq)
    # do
    #     history -d $i
    # done

#     FAILED_COMMANDS=
# }

# trap error_handler ERR
# trap debug_handler DEBUG
# trap exit_handler EXIT

export JAVA_HOME="C:\Program Files\Java\jdk-21.0.4.0.7-1"
export PATH="$JAVA_HOME/bin:$PATH"
export LANG=C.UTF-8
eval $(ssh-agent -s)
