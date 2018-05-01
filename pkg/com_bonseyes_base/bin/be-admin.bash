if [ -n "$ZSH_VERSION" ]; then
    autoload bashcompinit
    bashcompinit
    autoload compinit
    compinit
fi

eval "$(register-python-argcomplete3 be-admin)"

