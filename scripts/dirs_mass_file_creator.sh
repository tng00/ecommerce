#!/bin/bash

# Список имен для замены
names=("search" "review" "product" "permission" "order" "payment" "auth" "category")

# Цикл по каждому имени
for name in "${names[@]}"; do
    # Создаем папку для каждого имени
    mkdir -p "$name"
    # Создаем файлы внутри соответствующей папки
    touch "$name/test_${name}_service.py"
    touch "$name/test_${name}_repository.py"
    touch "$name/test_${name}_router.py"
done

echo "Все папки и файлы успешно созданы."