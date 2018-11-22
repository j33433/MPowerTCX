pyinstaller --clean -y --noupx --windowed -D ^
    --icon "..\images\mpowertcx icon flat.ico" ^
	--path C:\Users\User\Miniconda3-pip\Lib\site-packages\scipy\extra-dll ^
	--hidden-import scipy._lib.messagestream ^
	mpowertcx.py
