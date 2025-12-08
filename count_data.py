import json

# with open('geometry_finetune_clean.json', 'r', encoding="utf-8") as file:
with open('grok_finetune_dataset.json', 'r', encoding="utf-8") as file:
    data = json.load(file)
# sub_arr_47_66 = data[47:66]
# sub_arr_66_86 = data[66:86]
# sub_arr_86 = data[86:]
# print(data[49]['input'])
print(len(data))
# print(len(sub_arr_47_66)+len(sub_arr_66_86)+len(sub_arr_86))
# with open("output_47_66.json", "w", encoding="utf-8") as f:
#     json.dump(sub_arr_47_66, f, ensure_ascii=False, indent=2)
# with open("output_66_86.json", "w", encoding="utf-8") as f:
#     json.dump(sub_arr_66_86, f, ensure_ascii=False, indent=2)
# with open("output_86.json", "w", encoding="utf-8") as f:
#     json.dump(sub_arr_86, f, ensure_ascii=False, indent=2)