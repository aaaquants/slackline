from flask import Flask, render_template, request
# from gui.simple.gui_compute import compute
# from gui.simple.gui_model import InputForm
from gui.clenow.gui_model import InputForm
from gui.clenow.gui_compute import compute
from os.path import expanduser
from os import getcwd
home = getcwd()

app = Flask(__name__,template_folder=home)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = InputForm(request.form)
    if request.method == 'POST' and form.validate():
        print form.start.data,form.finish.data,form.symbols.data
        result = compute(form.start.data,form.finish.data,form.symbols.data,form.lr_lkbk.data,form.ma_lkbk.data,form.atr_lkbk.data,form.risk_factor.data,form.max_items.data)
    else:
        result = None

    # return render_template('gui/simple/gui_view.html', form=form, result=result)
    return render_template('gui/clenow/gui_view.html', form=form, result=result)

if __name__ == '__main__':
    app.run(debug=True)
