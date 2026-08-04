import json



# def match_config(args, url_path):
#     args_wash = []
#     for arg in args:
#         if str(arg).strip().startswith('-'):
#             continue
#         if str(arg).strip().startswith('./') or str(arg).strip().endswith('.\\'):
#             args_wash.append(arg.strip()[2:])
#             continue
#         args_wash.append(arg)
#     print('1111111111111')
#     print(''.join(args_wash).replace('\\', '/'))
#     print(url_path)
#     if url_path in ''.join(args_wash).replace('\\', '/'):
#         return True
#     else:
#         return False



def find_instructions(endpoint_module, config_path='./mcp_config.json'):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        # print(f'config: {config}')
        for key, value in config['mcpServers'].items():
            # print(abs_path.replace('\\', '/'))
            # print(value['args'])
            if endpoint_module in ''.join(value['args']):
                instructions = value['irCtl']['instructions']
                cmd_list = [c['cmdName'] for c in value['irCtl']['cmd']['rawCmdList']]
                if 'seqCmdList' in value['irCtl']['cmd']: cmd_list += [c['cmdName'] for c in value['irCtl']['cmd']['seqCmdList']]

                final_instructions = f'''{instructions}，可用命令：{'、'.join(cmd_list)}，操作设备时联系对话上下文，不要搞错了'''
                return final_instructions
    return None



if __name__ == '__main__':
    # abs_path = os.path.abspath(__file__)
    url_path = '/local_mcp/controller__air_conditioner__home_office'
    config_path = '../mcp_config.json'
    DEVICE_CONFIG = find_instructions(url_path, config_path)
    print(f'DEVICE_CONFIG: {DEVICE_CONFIG}')


