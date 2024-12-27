#!/bin/bash

# Список имен для замены
#names=("search" "review" "product" "permission" "order" "payment" "auth" "category")

names=("recsys" "predict_analysis")
# Цикл по каждому имени
for name in "${names[@]}"; do
    # Создаем файлы с нужными именами
    touch "${name}_service.py"
    touch "${name}_repository.py"
    touch "${name}_router.py"
    touch "${name}_schema.py"
    touch "${name}.py"

done

echo "Все файлы успешно созданы."