# PyInstaller spec template
block_cipher = None

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[],
             hiddenimports=collect_submodules('matplotlib') + collect_submodules('PyQt5'),
             hookspath=[],
             excludes=[],
             runtime_hooks=[],
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='chemical_visualizer',
          debug=False,
          strip=False,
          upx=True,
          console=True)
