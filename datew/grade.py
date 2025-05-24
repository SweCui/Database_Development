from flask import send_file
import pandas as pd

@main_bp.route('/grades/import', methods=['POST'])
def import_grades():
    if 'file' not in request.files:
        return "未选择文件", 400
    
    file = request.files['file']
    if file.filename.endswith('.xlsx'):
        df = pd.read_excel(file)
        # 处理成绩数据...
        return "导入成功"
    
    return "仅支持Excel文件", 400

@main_bp.route('/grades/export')
def export_grades():
    df = pd.read_sql('SELECT * FROM 成绩', db.engine)
    df.to_excel('grades.xlsx')
    return send_file('grades.xlsx', as_attachment=True)