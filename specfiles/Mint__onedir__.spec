# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['..\\scripts\\Mint.py'],
             pathex=['C:\\Users\\soere\\workspace\\ms-mint'],
             binaries=[],
             datas=[('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash\\favicon.ico', '.\\dash\\favicon.ico'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_html_components', '.\\dash_html_components'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_table', '.\\dash_table'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_tabulator', '.\\dash_tabulator'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_core_components', '.\\dash_core_components'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_renderer', '.\\dash_renderer'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_bootstrap_components', '.\\dash_bootstrap_components'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_html_components', '.\\dash_html_components'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_extensions', '.\\dash_extensions'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\dash_uploader', '.\\dash_uploader'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\plotly', '.\\plotly'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\pyopenms\\share', '.\\pyopenms\\share'),
                    ('C:\\Users\\soere\\anaconda3\\envs\\ms-mint\\lib\\site-packages\\pymzml', '.\\pymzml'),

                    ('C:\\Users\\soere\\workspace\\ms-mint\\static\\ChEBI.tsv', '.\\static'),                    
                    ],
             hiddenimports=['pkg_resources.py2_warn'],  
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Mint',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Mint')
