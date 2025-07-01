def get_address(device, index):
    tables = {
        'M': [
            {'range': (0, 255), 'address': ('0800', '08FF')},
            {'range': (256, 511), 'address': ('0900', '09FF')},
            {'range': (512, 767), 'address': ('0A00', '0AFF')},
            {'range': (768, 1023), 'address': ('0B00', '0BFF')},
        ],
        'D': [
            {'range': (0, 255), 'address': ('1000', '10FF')},
            {'range': (256, 511), 'address': ('1100', '11FF')},
            {'range': (512, 767), 'address': ('1200', '12FF')},
            {'range': (768, 1023), 'address': ('1300', '13FF')},
            {'range': (1024, 1279), 'address': ('1400', '14FF')},
            {'range': (1280, 1535), 'address': ('1500', '15FF')},
        ]
    }

    if device not in tables:
        return f"Device '{device}' not found."

    for entry in tables[device]:
        start, end = entry['range']
        if start <= index <= end:
            base_address_hex = entry['address'][0]
            offset = index - start
            full_address_hex = hex(int(base_address_hex, 16) + offset)[2:].upper().zfill(4)
            high_byte = full_address_hex[:2]
            low_byte = full_address_hex[2:]
            return {
                'device': f"{device}{index}",
                'hex_address': full_address_hex,
                'high_byte': high_byte,
                'low_byte': low_byte,
            }

    return f"Index {index} not found for device '{device}'."
