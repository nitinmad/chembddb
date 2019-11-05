from flask import Flask, render_template, url_for, request,redirect
import pymysql
import os
import sys
import pandas as pd
from copy import deepcopy
try:
    import pybel
except:
    from openbabel import pybel

from flask import send_from_directory
import numpy as np
import time


app = Flask(__name__)
upload_directory=os.getcwd()
app.config['UPLOAD FOLDER']=upload_directory

@app.route('/')
def begin():
    return redirect(url_for('connect'))

def connect_mysql(host,user,pw):
    global cur, con
    try:
        con = pymysql.connect(host = host, user=user, password = pw)
        cur = con.cursor()
        cur.execute('show databases;')
        all_dbs_tup=cur.fetchall()
        all_dbs = []
        for i in all_dbs_tup:
            if '_chembddb' in i[0]:
                m=i[0]
                all_dbs.append((m[:-9],))
        return cur,all_dbs
    except:
        return 'invalid','credentials'
    
@app.route('/connect',methods=['GET','POST'])
def connect():
    global cur,all_dbs
    """establishes mysql connection based on the credentials provided during setup; any changes in credentials should be made in credentails.dat

    Parameters
    ----------
    Returns
    -------
    cur: cursor object
        pointer to the MySQL database; used to execute all SQL queries
    """ 
    if request.method=='POST':
        cred=request.form
        cred = cred.to_dict(flat=False)
        cur,all_dbs = connect_mysql(host = cred['host'][0], user=cred['username'][0], pw = cred['password'][0])
        if cur == 'invalid' and all_dbs == 'credentials':
            return render_template('connect.html',err_msg='Invalid Credentials. Did not connect to MySQL')
        else:
            return render_template('connect.html',success_msg='Connection Established',host=cred['host'][0],user=cred['username'][0],password=cred['password'][0],all_dbs=all_dbs)
    else:
        return render_template('connect.html')
    
@app.route('/setup',methods=['GET','POST'])
def setup(host='',user='',pw='',db=''):
    """
    Function to setup the database with the chembddb schema

    Parameters
    ----------
    host: str default=''
        the hostname is the domain name or server name
    user: str default=''
        the username for mysql
    pw: str default=''
        the password for mysql
    db: str default=''
        the name of the database that needs to be set up

    """
    if host != '':
        b, a = connect_mysql(host=host,user=user,pw=pw)
        db = db +'_chembddb'
    elif request.method=='POST':
        db_details=request.form
        db_details=db_details.to_dict(flat=False)
        db=db_details['dbname'][0]+'_chembddb'
    else:
        all_dbs=[]
        cur.execute('show databases;')
        all_dbs_tup=cur.fetchall()
        for i in all_dbs_tup:
            if '_chembddb' in i[0]:
                m=i[0]
                all_dbs.append((m[:-9],))
        return render_template('setup.html',all_dbs=all_dbs)
    
    all_dbs=[]
    cur.execute('show databases;')
    all_dbs_tup=cur.fetchall()
    for i in all_dbs_tup:
        if '_chembddb' in i[0]:
            m=i[0]
            all_dbs.append((m[:-9],))
    cur.execute('USE INFORMATION_SCHEMA')
    result=cur.execute('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=\'%s\''%db)
    if result == 0:
        cur.execute('CREATE DATABASE %s;'%db)
        cur.execute('USE %s;'%db)
        cur.execute('CREATE TABLE `%s`.`Molecule` (`id` INT NOT NULL AUTO_INCREMENT,`SMILES_str` VARCHAR(500) DEFAULT \'NONE\', `InChI` VARCHAR(200) DEFAULT \'NONE\',`Molecule_identifier` VARCHAR(120) DEFAULT \'NONE\',`MW` FLOAT, PRIMARY KEY (`id`));'%db)
        # cur.execute('CREATE TABLE `%s`.`Credit`(`id` INT NOT NULL AUTO_INCREMENT,`DOI` VARCHAR(100) UNIQUE DEFAULT \'None\',`details` VARCHAR(100) DEFAULT \'None\',PRIMARY KEY (`id`));'%db)
        cur.execute('CREATE TABLE `%s`.`Property`(`id` INT NOT NULL AUTO_INCREMENT,`Property_str` VARCHAR(100) NOT NULL UNIQUE,`Unit` VARCHAR(100) NOT NULL,PRIMARY KEY (`id`));'%db)
        cur.execute('CREATE TABLE `%s`.`Model`(`id` INT NOT NULL AUTO_INCREMENT,`method_name` VARCHAR(100) NOT NULL UNIQUE,`options` VARCHAR(500),PRIMARY KEY (`id`));'%db)
        cur.execute('CREATE TABLE `%s`.`Functional`(`id` INT NOT NULL AUTO_INCREMENT,`name` VARCHAR(100) DEFAULT \'NONE\',PRIMARY KEY (`id`));'%db)
        cur.execute('CREATE TABLE `%s`.`Basis_set`(`id` INT NOT NULL AUTO_INCREMENT,`name` VARCHAR(100) DEFAULT \'NONE\',PRIMARY KEY (`id`));'%db)
        cur.execute('CREATE TABLE `%s`.`Forcefield`(`id` INT NOT NULL AUTO_INCREMENT,`name` VARCHAR(100) DEFAULT \'NONE\',PRIMARY KEY (`id`));'%db)
        # cur.execute('CREATE TABLE `%s`.`Topology`(`id` INT NOT NULL AUTO_INCREMENT,`geometry` VARCHAR(100) NOT NULL,`symbols` VARCHAR(100),`method` VARCHAR(100),`steps` INT,PRIMARY KEY (`id`));'%db)
        cur.execute('CREATE TABLE `%s`.`Value`(`id` INT NOT NULL AUTO_INCREMENT,`num_value` FLOAT NOT NULL,`model_id` INT NOT NULL,`property_id` INT NOT NULL,`molecule_id` INT NOT NULL,`functional_id` INT, `basis_id` INT,`forcefield_id` INT,PRIMARY KEY (`id`));'%db)

        cur.execute('ALTER TABLE `%s`.`Value` ADD CONSTRAINT `Value_fk0` FOREIGN KEY (`model_id`) REFERENCES `Model`(`id`) on DELETE CASCADE;'%db)
        cur.execute('ALTER TABLE `%s`.`Value` ADD CONSTRAINT `Value_fk1` FOREIGN KEY (`property_id`) REFERENCES `Property`(`id`) on DELETE CASCADE;'%db)
        cur.execute('ALTER TABLE `%s`.`Value` ADD CONSTRAINT `Value_fk2` FOREIGN KEY (`molecule_id`) REFERENCES `Molecule`(`id`) on DELETE CASCADE;'%db)
        cur.execute('ALTER TABLE `%s`.`Value` ADD CONSTRAINT `Value_fk3` FOREIGN KEY (`functional_id`) REFERENCES `Functional`(`id`) on DELETE CASCADE;'%db)
        cur.execute('ALTER TABLE `%s`.`Value` ADD CONSTRAINT `Value_fk4` FOREIGN KEY (`basis_id`) REFERENCES `Basis_set`(`id`) on DELETE CASCADE;'%db)
        cur.execute('ALTER TABLE `%s`.`Value` ADD CONSTRAINT `Value_fk5` FOREIGN KEY (`forcefield_id`) REFERENCES `Forcefield`(`id`) on DELETE CASCADE;'%db)
        cur.execute('show databases;')
        all_dbs_tup=cur.fetchall()
        all_dbs=[]
        for i in all_dbs_tup:
            if '_chembddb' in i[0]:
                m=i[0]
                all_dbs.append((m[:-9],))
        if host == '':
            return render_template('setup.html',dbname=db,all_dbs=all_dbs,success_msg='The database has been created.')
        else:
            print(all_dbs)
            return 'Success'
    else:
        if host == '':
            return render_template('setup.html',dbname=db,all_dbs=all_dbs,err_msg='Database already exists.')
        else:
            return 'Failed! Database already exists.'

@app.route('/insert',methods=['GET','POST'])
def insert(host='',user='',pw='',db='',smi_col='',mol_identifier='',conf_file='',data_file=''):
    """
    Function to insert data into an existing database

    Parameters
    ----------
    host: str default=''
        the hostname is the domain name or server name
    user: str default=''
        the username for mysql
    pw: str default=''
        the password for mysql
    db: str default=''
        the name of the database that needs to be set up
    smi_col: str default=''
        name/header of the smiles column in your data (csv) file 
    mol_identifier: str default=''
        name/header of any other molecule identifier in your data (csv) file
    conf_file: str default=''
        path to the file containing all the configurations/options (csv); property names should be the same as the column headers in your data (csv) file
    data_file: str default=''
        path to the file containing the data that needs to be entered into the database

    """
    mi_cols=[]
    cur.execute('show databases;') 
    all_dbs_tup=cur.fetchall()
    all_dbs=[]
    for i in all_dbs_tup:
        if '_chembddb' in i[0]:
            m=i[0]
            all_dbs.append((m[:-9],))
    if host !='':
        b,a = connect_mysql(host=host, user=user,pw=pw)
        db=db+'_chembddb'
    elif request.method=='POST':
        config_options=request.form
        config_options=config_options.to_dict(flat=False)
        db=config_options['dbname'][0]
        db = db+'_chembddb'
    else:
        return render_template('insert.html',all_dbs=all_dbs)
    
    cur.execute('USE INFORMATION_SCHEMA')
    result=cur.execute('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=\'%s\''%db)
    if result == 0:
        error_message='Database does not exist'
        if host == '':
            return render_template('insert.html',all_dbs=all_dbs,err_msg=error_message)
        else:
            return 'Failed! Database does not exists.'
    else:
        if type(conf_file) is str and conf_file=='':
            files=request.files
            files=files.to_dict(flat=False)
            conf_file=files['config_file'][0]
            data_file=files['data_file'][0]
            smi_col=config_options['smiles'][0]
            mol_identifier=config_options['molecule_identifier'][0]
            if conf_file.filename=='' or conf_file.filename.rsplit('.',1)[1]!='csv':
                db.replace('_chembddb','')
                db=db.replace('_',' ')
                if host == '':
                    return render_template('insert.html',title=db,err_msg='No config file provided or incorrect file format. (csv required)')
                else:
                    return 'Failed to insert all data! No config file provided or incorrect file format. (csv required)'
            elif data_file.filename=='' or data_file.filename.rsplit('.',1)[1]!='csv':
                db.replace('_chembddb','')
                db=db.replace('_',' ')
                if host == '':
                    return render_template('insert.html',title=db,err_msg='No data file provided or incorrect file format. (csv required)')
                else:
                    return 'Failed to insert all data! No data file provided or incorrect file format. (csv required)'
            elif smi_col=='' and mol_identifier=='':
                db.replace('_chembddb','')
                db=db.replace('_',' ')
                if host == '':
                    return render_template('insert.html',title=db,err_msg='No molecule identifiers provided.')
                else:
                    return 'No molecule identifiers provided'
            conf=pd.read_csv(conf_file)
            data=pd.read_csv(data_file)

        elif type(conf_file) is str and conf_file!='':
            if os.path.exists(conf_file) == False:
                return 'Failed! Config file does not exist in the path specified'
            if os.path.exists(data_file) == False:
                return 'Failed! Data file does not exist in the path specified.'

            conf=pd.read_csv(conf_file)
            data=pd.read_csv(data_file)
        else:
            conf = conf_file    
            data = data_file

        conf.replace(np.nan,'na',inplace=True)
        all_prop=True
        all_mols=True
        for prop in conf['properties']:
            if prop not in data.columns:
                all_prop=False
        if all_prop==False:
            db=db.replace('_',' ')
            if host=='':
                return render_template('insert.html',title=db,all_dbs=all_dbs,err_msg='Property(s) in config file do not exist in data.')
            else:
                return 'Failed! Property(s) in config file do not exist in data.'
        else:
            if smi_col!='' and smi_col not in data.columns:
                all_mols=False
            if mol_identifier!='' and mol_identifier not in data.columns:
                all_mols=False
            if all_mols==False:
                if host=='':
                    db=db.replace('_chembddb','')
                    db=db.replace('_',' ')
                    return render_template('insert.html',title=db,all_dbs=all_dbs,err_msg='Identifier(s) listed do not exist in data.')
                else:
                    return 'Failed! Identifier(s) listed do not exist in data.'
            else:
                cur.execute('USE %s;'%db)
                db = db.replace('_chembddb','')
                # loop throught he CSV file, check if the smiles value is in the table, if yes, fetch the corresponding id, same goes for property, same goes for method for that property, if it does not exist, fetch the last id and create a new entry

                # populating and property table
                entered_list=[]
                cur.execute("SELECT Property_str from Property")
                properties = cur.fetchall()
                for prop, units in zip(conf['properties'],conf['units']):
                    if any(prop in i for i in properties) or prop in entered_list:
                        pass
                    else:
                        entered_list.append(prop)
                        cur.execute("INSERT INTO Property(Property_str,Unit) VALUES(%s,%s)",[prop,units])
                # print('property table populated')
                # populating the model table
                cur.execute("SELECT Method_name from Model")
                models = cur.fetchall()
                entered_list=[]
                for method in conf['methods']:
                    if any(method in i for i in models) or method in entered_list:
                        pass
                    else:
                        entered_list.append(method)
                        cur.execute("INSERT INTO Model(Method_name) VALUES(%s)",[method])
                # print('method table populated')
                # populating the functional table
                ####testing####
                cur.execute('show tables;')
                tabs=cur.fetchall()
                print(tabs)
                ####testing####
                cur.execute("SELECT name FROM Functional")
                functionals = cur.fetchall()
                entered_list = []
                for func in conf['functional']:
                    if any(func in i for i in functionals) or func in entered_list:
                        pass
                    else:
                        entered_list.append(func)
                        cur.execute("INSERT INTO Functional(name) VALUES(%s)",[func])
                # print('functional table populated')
                # populating the basis_set table
                cur.execute("SELECT name FROM Basis_set")
                basis_sets = cur.fetchall()
                entered_list = []
                for basis in conf['basis']:
                    if any(basis in i for i in basis_sets) or basis in entered_list:
                        pass
                    else:
                        entered_list.append(basis)
                        cur.execute("INSERT INTO Basis_set(name) VALUES(%s)",[basis])

                # print('basis table populated')
                # populating the forcefield table
                cur.execute("SELECT name FROM Forcefield")
                forcefields = cur.fetchall()
                entered_list = []
                for ff in conf['forcefield']:
                    if any(ff in i for i in forcefields) or ff in entered_list or ff=='None':
                        pass
                    else:
                        entered_list.append(basis)
                        cur.execute("INSERT INTO Forcefield(name) VALUES(%s)",[ff])
                # print('ff table populated')
                # populating the molecule table
                cur.execute("SELECT SMILES_str,Molecule_identifier,MW from Molecule")
                molecules = cur.fetchall()
                new_entries=[]
                # check last id for molecule, add molecule index, melt dataframe, add property and method index using lambda and dictionary
                # check for molecule identifier (name, IUPAC, )
                
                for mol in range(len(data)):
                    if smi_col=='':
                        if data.loc[mol][mol_identifier] not in new_entries:
                            new_entries.append(('None',data.loc[mol][mol_identifier],'None'))
                    elif mol_identifier=='':
                        if data.loc[mol][smi_col] not in new_entries:
                            try:
                                m = pybel.readstring("smiles",data.loc[mol][smi_col])
                                smiles = m.write('can').strip()
                                mw = m.molwt
                                mw = round(mw,3)
                            except:
                                db=db.replace('_',' ')
                                if host!='':
                                    return 'Failed, Invalid SMILES at position %d.'%str(mol)
                                else:
                                    return render_template('insert.html',title=db,all_dbs=all_dbs,err_msg='Invalid SMILES at position %d.'%str(mol))
                            new_entries.append((smiles,'None',mw))
                    else:
                        try:
                            m = pybel.readstring("smiles",data.loc[mol][smi_col])
                            smiles = m.write('can').strip()
                            mw = m.molwt
                            mw = round(mw,3)
                        except:
                            db=db.replace('_',' ')
                            if host!='':
                                return 'Failed, Invalid SMILES at position %d.'%str(mol)
                            else:
                                return render_template('insert.html',title=db,all_dbs=all_dbs,err_msg='Invalid SMILES at position %d.'%str(mol))
                        new_entries.append((smiles,data.loc[mol][mol_identifier],mw))

                # temporary fix to enable for case-insensitivity in molecule-identifier
                molecules = [list(x) for x in molecules]
                new_entries = [list(x) for x in new_entries]
                for i in molecules:
                    i[1] = i[1].lower()
                for i in new_entries:
                    i[1] = i[1].lower()
                molecules = tuple(tuple(x) for x in molecules)
                new_entries = tuple(tuple(x) for x in new_entries)
                required_entries = list(set(new_entries) - set(molecules))
                cur.executemany('INSERT INTO Molecule(SMILES_str,Molecule_identifier,MW) VALUE(%s,%s,%s)',required_entries)
                # print('molecule table populated')
                # populating the credit table
                # todo: figure out how to deal with the credit/publication
                # cur.execute('INSERT INTO %s.Credit(DOI) VALUES(%s)'%db,' ')
                cols=list(conf.properties)
                if smi_col!='':
                    cols.append(smi_col)
                if mol_identifier!='':
                    cols.append(mol_identifier)
                data = data[cols]
                # populating the values table

                cur.execute('SELECT id,Property_str from Property')
                all_props = cur.fetchall()
                prop_id = dict(map(reversed,all_props))
                cur.execute('SELECT id,Method_name from Model')
                all_models = cur.fetchall()
                model_id = dict(map(reversed,all_models))
                cur.execute('SELECT id,name from Functional')
                all_functionals = cur.fetchall()
                functional_id=dict(map(reversed,all_functionals))
                cur.execute('SELECT id,name from  Basis_set')
                all_basis = cur.fetchall()
                basis_id = dict(map(reversed,all_basis))
                cur.execute('SELECT id,name from Forcefield')
                all_ff = cur.fetchall()
                ff_id = dict(map(reversed,all_ff))
                if smi_col=='':
                    cur.execute("SELECT id,Molecule_identifier from Molecule") 
                    all_mols = cur.fetchall()
                    molecule_id = dict(map(reversed,all_mols))
                    data['molecule_id']=data[mol_identifier].apply(lambda a: molecule_id[a])
                else:
                    cur.execute("SELECT id,SMILES_str from Molecule")
                    all_mols = cur.fetchall()
                    molecule_id = dict(map(reversed,all_mols))
                    data['molecule_id']=data[smi_col].apply(lambda a: molecule_id[pybel.readstring('smi',a).write('can').strip()])
                
                molecule_id = dict(map(reversed,all_mols))
                if mol_identifier!='':
                    data.drop(mol_identifier,1,inplace=True)
                if smi_col!='':
                    data.drop(smi_col,1,inplace=True)
                data = data.melt('molecule_id')
                data['property_id']=data['variable'].apply(lambda a: prop_id[a])
                data['model_id']=data['variable'].apply(lambda a: model_id[conf.loc[conf['properties'].tolist().index(a)]['methods']])
                data['functional_id']=data['variable'].apply(lambda a: functional_id[conf.loc[conf['properties'].tolist().index(a)]['functional']])
                data['basis_id']=data['variable'].apply(lambda a: basis_id[conf.loc[conf['properties'].tolist().index(a)]['basis']])
                data['ff_id']=data['variable'].apply(lambda a: ff_id[conf.loc[conf['properties'].tolist().index(a)]['forcefield']])
                data.drop('variable',1,inplace=True)
                to_drop = []
                id = tuple(data['molecule_id'])
                cur.execute('select * from Value where molecule_id in {}'.format(str(id)))
                vals = cur.fetchall()
                vals = [list(x) for x in vals]
                vals = pd.DataFrame(vals, columns=['id','value','model_id', 'property_id','molecule_id', 'functional_id','basis_id','ff_id'])
                check_data = data.drop('value',1)
                vals = vals[check_data.columns]
                vals = [list(vals.loc[x]) for x in range(len(vals))]
                for i in range(len(data)):
                    if list(check_data.loc[i]) in vals:
                        to_drop.append(i)
                data.drop(to_drop,0,inplace=True)

                if len(data) == 0:
                    if host=='':
                        return render_template('insert.html',title=db,all_dbs=all_dbs,err_msg='Duplicates entries for all molecules exist.')
                    else:
                        return 'Failed! Duplicate entries for all molecules exist.'
                else:
                    cur.executemany('INSERT INTO Value(molecule_id,num_value,property_id,model_id,functional_id,basis_id,forcefield_id) VALUES(%s,%s,%s,%s,%s,%s,%s)',data.values.tolist())
                    # print('value table populated')
                    con.commit()
                    db=db.replace('_chembddb','')
                    db=db.replace('_',' ')
                    if host=='':
                        if to_drop != []:
                            return render_template('insert.html',title=db,all_dbs=all_dbs,err_msg='A few molecules were not entered due to duplicate entries',success_msg='The database has been successfully populated')
                        else:
                            return render_template('insert.html',title=db,all_dbs=all_dbs,success_msg='The database has been successfully populated')
                    else:
                        if to_drop != []:
                            return 'A few molecules were not entered due to duplicate entries but the database was successfully populated with the rest'
                        else:
                            return 'Successfully entered the data into the database'

@app.route('/search',methods=['GET','POST'])
def search():
    return render_template('search.html',all_dbs=all_dbs)

@app.route('/search_db<db>',methods=['GET','POST'])
def search_db(db):
    all_dbs=[]
    cur.execute('show databases;')
    all_dbs_tup=cur.fetchall()
    for i in all_dbs_tup:
        if '_chembddb' in i[0]:
            m=i[0]
            all_dbs.append((m[:-9],))
    db=db[1:-1]
    db=db+'_chembddb'
    cur.execute('USE INFORMATION_SCHEMA')
    result=cur.execute('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=\'%s\''%db)
    if result == 0:
        error_message='Database does not exist'
        return render_template('Search.html',all_dbs=all_dbs,err_msg=error_message)
    else:
        cur.execute('USE %s'%db)
        db = db.replace('_chembddb','')
        cur.execute('Select * from Property')
        properties=cur.fetchall()
        cur.execute('Select id,method_name from Model')
        results=cur.fetchall()
        cur.execute("Select * from Functional")
        functionals=cur.fetchall()
        cur.execute("Select * from basis_set")
        basis_sets=cur.fetchall()
        cur.execute("Select * from forcefield")
        forcefields=cur.fetchall()
        methods=[]
        global search_results
        global sql
        global ini
        global fin
        global n_res
        global noprev
        global nonext
        is_download=True
        to_order=True
        for i in results:
            methods.append(i[1])
        if request.method == 'POST' and 'search-query' in request.form:
            from_form = request.form
            sql='select value.molecule_id,molecule.SMILES_str,model.method_name,functional.name,basis_set.name,forcefield.name,Property.Property_str, value.num_value from molecule inner join Value on molecule.id=value.molecule_id inner join property on property.id=value.property_id inner join model on model.id=value.model_id inner join functional on functional.id=value.functional_id inner join basis_set on basis_set.id = value.basis_id inner join forcefield on forcefield.id=value.forcefield_id where '
            from_form = from_form.to_dict(flat=False)
            keys=[i for i in from_form if '_id' in i]
            min_max_err=False
            min_max_prop=[]
            props=[]
            p = []
            # tuple of tuples to list of tuples
            for pr in properties:
                p.append(list(pr))
            properties = p
            if len(keys)>0:
                for k in keys:
                    prop_id=int(from_form[k][0])
                    props.append(prop_id)
                    from_val=float(from_form[k[:-3]+'_from_val'][0])
                    to_val=float(from_form[k[:-3]+'_to_val'][0])
                    properties[prop_id-1].append(from_val)
                    properties[prop_id-1].append(to_val)
                    if from_val > to_val:
                        min_max_err=True
                    sql = sql[:sql.rfind('where')+6] + 'molecule_id in (select molecule_id from value where value.property_id={0} and value.num_value>{1} and value.num_value<{2}) and '.format(prop_id,from_val,to_val) + sql[sql.rfind('where')+6:]
                if len(keys)!=0:
                    sql=sql[:-5]
                valsid=' and value.property_id in '
                for i in range(len(props)):
                    if i > 0:
                        valsid = valsid + ',' + str(props[i])
                    else:
                        valsid = valsid + '(' + str(props[i])
                valsid = valsid +')'
                sql = sql +valsid
            MW_to = None
            if 'MW' in from_form:
                from_val=float(from_form['MW_from_val'][0])
                to_val=float(from_form['MW_to_val'][0])
                MW_from = from_val
                MW_to = to_val
                if from_val > to_val:
                    min_max_err=True
                if len(keys)!=0:
                    sql=sql+" and molecule.MW > {} and molecule.MW < {}".format(float(from_form['MW_from_val'][0]),float(from_form['MW_to_val'][0]))
                else:
                    sql=sql+" molecule.MW > {} and molecule.MW < {}".format(float(from_form['MW_from_val'][0]),float(from_form['MW_to_val'][0]))
                    keys.append('MW')

            if 'smiles_search' in from_form:
                if len(keys)==0:
                    sql=sql[:-6]
            
            if 'method' in from_form:
                met_id=0
                for m in results:
                    if m[1]==from_form['method_name'][0]:
                        met_id=m[0]
                if len(keys)==0:
                    sql=sql+" Value.model_id = {}".format(met_id)
                else:
                    sql=sql+" and Value.model_id ={}".format(met_id)

            if 'func' in from_form:
                if len(keys)==0:
                    sql=sql+' Value.functional_id={}'.format(from_form['functional_name'][0])
                else:
                    sql=sql+' and Value.functional_id={}'.format(from_form['functional_name'][0])
            
            if 'basis' in from_form:
                if len(keys)==0:
                    sql=sql+' Value.basis_id={}'.format(from_form['basis_set'][0])
                else:
                    sql=sql+' and Value.basis_id={}'.format(from_form['basis_set'][0])
            
            if 'ff' in from_form:
                if len(keys)==0:
                    sql=sql+' Value.forcefield_id={}'.format(from_form['forcefield'][0])
                else:
                    sql=sql+' and Value.forcefield_id={}'.format(from_form['forcefield'][0])
            
            counts_q = 'select count(*) '+sql[sql.find('from'):] +';'
            sql = sql + 'limit 50'
            cur.execute(counts_q)
            global counts
            counts = cur.fetchall()
            counts = counts[0][0]
            sql=sql+';'
            temp_col=[]              
            temp_met=[]
            if counts == 0:
                if min_max_err==True:
                    n_res = 'Min value entered is > Max value entered for one of the fields above.' 
                    columns=''
                else:               
                    n_res = 'Number of results='+ str(counts)+'. No such candidates exist in your database'
                    columns=''
                if 'MW' in from_form:
                    return render_template('search_db.html',MW_from=MW_from, MW_to=MW_to,properties=properties,columns=columns,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db)
                else:
                    return render_template('search_db.html',properties=properties,columns=columns,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db)
            else:
                cur.execute(sql)
                data1=cur.fetchall() 
                data = pd.DataFrame(list(data1), columns=['Molecule_id','SMILES','Method','Functional','Basis_set','forcefield','Property','Value'])
                data['ID_SMI']=data['Molecule_id'].astype(str)+','+data['SMILES']
                data['Property']=data['Property']+'-' +data['Method']+'('+data['Functional']+'/'+data['Basis_set']+')('+data['forcefield']+')'
                data = data[data.columns[-3:]]
                data=data.pivot_table(index='ID_SMI',columns='Property',values='Value')
                data = data.reset_index()
                data[['ID','SMILES']]=data['ID_SMI'].str.split(',',expand=True)
                columns=['ID','SMILES']

                for i in data.columns[1:-2]:
                    columns.append(i)
                data=data[columns]
                columns=[c.replace('(NA/NA)','') for c in columns]
                columns=[c.replace('(na/na)','') for c in columns]
                columns=[c.replace('(NA)','') for c in columns]
                columns=[c.replace('(na)','') for c in columns]
                search_results = data              
                search_results.columns = columns
                for c in columns:
                    if '-' in c:
                        temp_col.append(c.split('-')[0])
                        if len(c.split('-'))>2:
                            temp_met.append(c.split('-')[1]+'-'+c.split('-')[2])
                        else:
                            temp_met.append(c.split('-')[1])
                    else:
                        temp_col.append(c)
                        temp_met.append('')
                try:
                    smi_val = None
                    if 'smiles_search' in from_form:
                        smarts = pybel.Smarts(from_form['smiles'][0])
                        smi_val = smarts
                        for i in range(len(data)):
                            mol = pybel.readstring("smi",data.loc[i]['SMILES'])
                            smarts.obsmarts.Match(mol.OBMol)
                            if len(smarts.findall(mol))==0:
                                data.drop(i,0,inplace=True)
                        if len(data)==0:
                            n_res='Number of results='+ str(len(data))+'\nNo such candidates exist in your database'
                        else:
                            n_res=len(data)
                    else:
                        n_res=counts                       
                except:
                    n_res='Invalid Smarts entered'
                    data=pd.DataFrame()
                desc=['','']
                columns =[]
                for i in range(len(temp_met)):
                    columns.append((temp_col[i],temp_met[i]))
                for i in data.columns[2:]:
                    desc.append('mean={}, std={}, min={}, max={}'.format(data[i].describe()['mean'].round(2),data[i].describe()['std'].round(2),data[i].describe()['min'].round(2),data[i].describe()['max'].round(2)))
                kc = False
                for i in keys:
                    if '_id' in i:
                        kc = True
                if kc == False:
                    data=data[data.columns[:2]]
                    columns=columns[:2]
                    desc = desc[:2]
                data = tuple(data.itertuples(index=False,name=None))
                is_download=False
                to_order=False
                noprev=True
                db = db.replace('_chembddb','')
                ini=0
                if type(n_res) != str and n_res < 50:
                    fin = n_res
                    nonext=True
                else:
                    nonext=False
                    fin = 50
                if 'MW' in from_form:
                    return render_template('search_db.html',ini=ini,fin=fin, MW_from=MW_from, MW_to=MW_to,data = data,properties=properties,columns=columns,temp_met=temp_met,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db,desc=desc,noprev=noprev,nonext=nonext)
                else:
                    return render_template('search_db.html',ini=0,fin=fin,data = data,properties=properties,columns=columns,temp_met=temp_met,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db,desc=desc,noprev=noprev,nonext=nonext)
        elif 'next-50' in request.form:
            nonext=False
            counts = counts - 50
            from_form = request.form
            from_form = from_form.to_dict(flat=False)
            n_res_done = 0
            if sql[-9:] == 'offset 0;':
                sql = sql[:-9] + ';'
            elif ' offset' in sql:
                # checking the offset in the previous sql query, this number tells us how many results have been displayed already
                n_res_done = int(sql[-4:-1])
                sql = sql[:-4] + ' '+str(n_res_done + 50) +';'
                n_res_done = n_res_done + 50
            else:
                n_res_done = 50
                sql = sql[:-1]+' offset 50;'
            cur.execute(sql)
            data1=cur.fetchall() 
            data = pd.DataFrame(list(data1), columns=['Molecule_id','SMILES','Method','Functional','Basis_set','forcefield','Property','Value'])
            data['ID_SMI']=data['Molecule_id'].astype(str)+','+data['SMILES']
            data['Property']=data['Property']+'-' +data['Method']+'('+data['Functional']+'/'+data['Basis_set']+')('+data['forcefield']+')'
            data = data[data.columns[-3:]]
            temp_col=[]
            temp_met=[]
            if len(data)>0:
                data=data.pivot_table(index='ID_SMI',columns='Property',values='Value')
                data = data.reset_index()
                data[['ID','SMILES']]=data['ID_SMI'].str.split(',',expand=True)
                columns=['ID','SMILES']
                for i in data.columns[1:-2]:
                    columns.append(i)
                data=data[columns]
                columns=[c.replace('(NA/NA)','') for c in columns]
                columns=[c.replace('(na/na)','') for c in columns]
                columns=[c.replace('(NA)','') for c in columns]
                columns=[c.replace('(na)','') for c in columns]

                for c in columns:
                    if '-' in c:
                        temp_col.append(c.split('-')[0])
                        if len(c.split('-'))>2:
                            temp_met.append(c.split('-')[1]+'-'+c.split('-')[2])
                        else:
                            temp_met.append(c.split('-')[1])
                    else:
                        temp_col.append(c)
                        temp_met.append('')
                try:
                    smi_val = None
                    if 'smiles_search' in from_form:
                        smarts = pybel.Smarts(from_form['smiles'][0])
                        smi_val = smarts
                        for i in range(len(data)):
                            mol = pybel.readstring("smi",data.loc[i]['SMILES'])
                            smarts.obsmarts.Match(mol.OBMol)
                            if len(smarts.findall(mol))==0:
                                data.drop(i,0,inplace=True)
                    search_results=data
                    search_results.columns=columns
                    if len(data)==0:
                        n_res='Number of results='+ str(len(data))+'\nNo such candidates exist in your database'
                    else:
                        n_res=counts + n_res_done            
                except:
                    n_res='Invalid Smarts entered'
                    data=pd.DataFrame()
            else:
                # if min_max_err==True:
                #     n_res = 'Min value entered is > Max value entered for one of the fields above.' 
                #     columns=''
                # else:               
                n_res = 'Number of results='+ str(len(data))+'. No such candidates exist in your database'
                columns=''
            desc=['','']
            columns =[]
            if counts < 50: 
                fin = n_res_done + counts
                nonext = True
            else:
                nonext = False
                fin = n_res_done + 50                
            noprev=False
            if temp_met!=[]:
                for i in range(len(temp_met)):
                    columns.append((temp_col[i],temp_met[i]))
                for i in data.columns[2:]:
                    desc.append('mean={}, std={}, min={}, max={}'.format(data[i].describe()['mean'].round(2),data[i].describe()['std'].round(2),data[i].describe()['min'].round(2),data[i].describe()['max'].round(2)))
            if 'MW' in sql and 'value.property_id=' not in sql:
                columns = columns[:2]
                data = data[data.columns[:2]]
                desc = ['','']
            data = tuple(data.itertuples(index=False,name=None))
            ini = n_res_done
            if 'MW' in sql and 'value.property_id=' not in sql:
                return render_template('search_db.html',ini=ini,fin=fin, noprev=False,nonext=nonext,data = data,properties=properties,columns=columns,temp_met=temp_met,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db,desc=desc)
            else:
                return render_template('search_db.html',ini=ini,fin=fin,nonext=nonext,noprev=False,data = data,properties=properties,columns=columns,temp_met=temp_met,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db,desc=desc)
        elif 'prev-50' in request.form:
            noprev=False
            counts = counts + 50
            from_form = request.form
            from_form = from_form.to_dict(flat=False)
            n_res_done = 0
            if ' offset' in sql:
                # checking the offset in the previous sql query, this number tells us how many results have been displayed already
                n_res_done = int(sql[-4:-1])
                sql = sql[:-4] + ' '+str(n_res_done - 50) +';'
                n_res_done = n_res_done - 50
                noprev = False
            else:
                noprev = True

            if n_res_done ==0:
                noprev = True
            cur.execute(sql)
            data1=cur.fetchall() 
            data = pd.DataFrame(list(data1), columns=['Molecule_id','SMILES','Method','Functional','Basis_set','forcefield','Property','Value'])
            data['ID_SMI']=data['Molecule_id'].astype(str)+','+data['SMILES']
            data['Property']=data['Property']+'-' +data['Method']+'('+data['Functional']+'/'+data['Basis_set']+')('+data['forcefield']+')'
            data = data[data.columns[-3:]]
            temp_col=[]
            temp_met=[]
            if len(data)>0:
                data=data.pivot_table(index='ID_SMI',columns='Property',values='Value')
                data = data.reset_index()
                data[['ID','SMILES']]=data['ID_SMI'].str.split(',',expand=True)
                columns=['ID','SMILES']
                for i in data.columns[1:-2]:
                    columns.append(i)
                data=data[columns]
                columns=[c.replace('(NA/NA)','') for c in columns]
                columns=[c.replace('(na/na)','') for c in columns]
                columns=[c.replace('(NA)','') for c in columns]
                columns=[c.replace('(na)','') for c in columns]

                for c in columns:
                    if '-' in c:
                        temp_col.append(c.split('-')[0])
                        if len(c.split('-'))>2:
                            temp_met.append(c.split('-')[1]+'-'+c.split('-')[2])
                        else:
                            temp_met.append(c.split('-')[1])
                    else:
                        temp_col.append(c)
                        temp_met.append('')
                try:
                    smi_val = None
                    if 'smiles_search' in from_form:
                        smarts = pybel.Smarts(from_form['smiles'][0])
                        smi_val = smarts
                        for i in range(len(data)):
                            mol = pybel.readstring("smi",data.loc[i]['SMILES'])
                            smarts.obsmarts.Match(mol.OBMol)
                            if len(smarts.findall(mol))==0:
                                data.drop(i,0,inplace=True)
                    search_results=data
                    search_results.columns=columns
                    if len(data)==0:
                        n_res='Number of results='+ str(len(data))+'\nNo such candidates exist in your database'
                    else:
                        n_res=counts + n_res_done            
                except:
                    n_res='Invalid Smarts entered'
                    data=pd.DataFrame()
            else:
                n_res = 'Number of results='+ str(len(data))+'. No such candidates exist in your database'
                columns=''
            desc=['','']
            columns =[]
            fin = n_res_done + 50       
            if temp_met!=[]:
                for i in range(len(temp_met)):
                    columns.append((temp_col[i],temp_met[i]))
                for i in data.columns[2:]:
                    desc.append('mean={}, std={}, min={}, max={}'.format(data[i].describe()['mean'].round(2),data[i].describe()['std'].round(2),data[i].describe()['min'].round(2),data[i].describe()['max'].round(2)))
            
            if 'MW' in sql and 'value.property_id=' not in sql:
                columns = columns[:2]
                data = data[data.columns[:2]]
                desc = ['','']
            data = tuple(data.itertuples(index=False,name=None))
            ini = n_res_done
            if 'MW' in sql and 'value.property_id=' not in sql:
                return render_template('search_db.html',ini=n_res_done,fin=fin,noprev = noprev, nonext=False,data = data,properties=properties,columns=columns,temp_met=temp_met,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db,desc=desc)
            else:
                return render_template('search_db.html',ini=n_res_done,fin=fin, noprev = noprev,nonext=False,data = data,properties=properties,columns=columns,temp_met=temp_met,methods=methods,is_download=is_download,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db,desc=desc)        
        elif 'download_csv' in request.form:
            from_form = request.form
            from_form = from_form.to_dict(flat=False)
            desc=['','']
            for i in search_results.columns[2:]:
                desc.append('mean={}, std={}, min={}, max={}'.format(search_results[i].describe()['mean'].round(2),search_results[i].describe()['std'].round(2),search_results[i].describe()['min'].round(2),search_results[i].describe()['max'].round(2)))
            search_results.to_csv('results.csv',index=None)
            msg='Results have been downloaded as results.csv'
            data = tuple(search_results.itertuples(index=False,name=None))
            columns=[]
            for i in range(len(search_results.columns)):
                if i<2:
                    columns.append((search_results.columns[i],''))
                else:
                    if len(search_results.columns[i].split('-')) > 2:
                        columns.append((search_results.columns[i].split('-')[0],search_results.columns[i].split('-')[1]+'-'+search_results.columns[i].split('-')[2]))
                    else:
                        columns.append((search_results.columns[i].split('-')[0],search_results.columns[i].split('-')[1]))            
            return render_template('search_db.html',data = data,ini=ini, fin=fin, properties=properties,columns=columns,methods=methods,msg=msg,n_res=n_res,functionals=functionals,basis=basis_sets,forcefields=forcefields,is_download=is_download,all_dbs=all_dbs,noprev=noprev,nonext=nonext,title=db,desc=desc)
        elif 'orderby_property' in request.form:
            from_form=request.form
            from_form = from_form.to_dict(flat=False)
            if 'ascending' in from_form['select_order']:
                search_results=search_results.sort_values(by=from_form['property_orderby'])
            else:
                search_results=search_results.sort_values(by=from_form['property_orderby'],ascending=False)
            desc=['','']
            data = tuple(search_results.itertuples(index=False,name=None))
            for i in search_results.columns[2:]:
                desc.append('mean={}, std={}, min={}, max={}'.format(search_results[i].describe()['mean'].round(2),search_results[i].describe()['std'].round(2),search_results[i].describe()['min'].round(2),search_results[i].describe()['max'].round(2)))
            columns=[]
            for i in range(len(search_results.columns)):
                if i<2:
                    columns.append((search_results.columns[i],''))
                else:
                    if len(search_results.columns[i].split('-')) > 2:
                        columns.append((search_results.columns[i].split('-')[0],search_results.columns[i].split('-')[1]+'-'+search_results.columns[i].split('-')[2]))
                    else:
                        columns.append((search_results.columns[i].split('-')[0],search_results.columns[i].split('-')[1]))
            return render_template('search_db.html',data = data,properties=properties,ini=ini,fin=fin,noprev=noprev,nonext=nonext,columns=columns,methods=methods,n_res=n_res,basis=basis_sets,functionals=functionals,forcefields=forcefields,all_dbs=all_dbs,title=db,desc=desc)        
        else:
            return render_template('search_db.html',properties=properties,methods=methods,is_download=is_download,basis=basis_sets, functionals=functionals, forcefields=forcefields,all_dbs=all_dbs,title=db)

@app.route('/molecule-<dbid>',methods=['GET','POST'])
def molecule(dbid):
    
    # cur,conn=connect_mysql()
    import urllib.parse
    
    db=dbid.split('-')[0]
    db=db.replace(' ','_')
    id=dbid.split('-')[1]
    sql = 'SELECT Molecule.id, Molecule.MW, Molecule.SMILES_str,Molecule.Molecule_identifier,Property.Property_str, Property.Unit, Model.method_name,  Functional.name, Basis_set.name,forcefield.name, Value.num_value from Molecule inner join value on Molecule.id=Value.Molecule_id inner join Property on Property.id=VALUE.property_id INNER JOIN Model on Value.model_id=Model.id inner join functional on functional.id=value.functional_id inner join basis_set on basis_set.id=value.basis_id inner join forcefield on forcefield.id=value.forcefield_id where Molecule.id={}'.format(id)
    db=db+'_chembddb'
    cur.execute('USE {};'.format(db))
    cur.execute(sql)
    result=cur.fetchall()
    mol_data=pd.DataFrame(list(result),columns=['ID','MW','SMILES','Identifier','Property','Unit','Method','Functional','Basis_set','Forcefield','Value'])
    mol_data['ALL']=mol_data['ID'].astype(str) +',;'+mol_data['MW'].astype(str)+',;'+mol_data['SMILES']+',;'+mol_data['Identifier']
    mol_data['Property(Unit)']=mol_data['Property']+' ('+mol_data['Unit']+')\n'+'- '+mol_data['Method']+'('+mol_data['Functional']+'/'+mol_data['Basis_set']+')('+mol_data['Forcefield']+')'
    mol_data=mol_data[['ALL','Property(Unit)','Value']]
    mol_data=mol_data.pivot(index='ALL',columns='Property(Unit)')
    mol_data=mol_data['Value'].reset_index()
    mol_data[['ID','MW','SMILES','Identifier']]=mol_data['ALL'].str.split(',;',expand=True)
    url_smi = urllib.parse.quote_plus(mol_data['SMILES'][0])
    cols=['ID','MW','SMILES','Identifier']
    for i in mol_data.columns[1:-4]:
        cols.append(i)
    mol_data=mol_data[cols]
    mol_ob = pybel.readstring("smi",mol_data['SMILES'][0])
    mymol = pybel.readstring("smi", mol_ob.write("can"))
    mymol.make3D(forcefield='mmff94', steps=50)
    mymol.write('xyz',app.config['UPLOAD FOLDER']+'/chembddb_{}.xyz'.format(mol_data['ID'][0]),overwrite=True)
    cols=[c.replace('(na/na)','') for c in cols]
    cols=[c.replace('(na)','') for c in cols]
    cols=[c.replace('(na)','') for c in cols]
    mol_data = tuple(mol_data.itertuples(index=False,name=None))
    mol_data = (tuple(cols[:]),)+mol_data
    mol_data=tuple(zip(*mol_data))
    db=db.replace('_',' ')
    return render_template('molecule.html',mol_data=mol_data,columns=cols,title=db,all_dbs=all_dbs,url_smi=url_smi)

@app.route('/delete',methods=['GET','POST'])
def delete(host='',user='',pw='',db=''):
    """
    Delete a database that was created using chembddb or delete data from one.

    Parameters
    ----------
    host: str default=''
        the hostname is the domain name or server name
    user: str default=''
        the username for mysql
    pw: str default=''
        the password for mysql
    db: str default=''
        the name of the database that needs to be set up

    """
    if db !='':
        try:
            db = db+'_chembddb'
            a,b = connect_mysql(host=host,user=user,pw=pw)
            cur.execute('drop database %s;'%db)
            return 'Successfully deleted the database'
        except:
            return 'Failed! database does not exist'
    else:
        cur.execute('show databases;')
        all_dbs=[]
        all_dbs_tup=cur.fetchall()
        for i in all_dbs_tup:
            if '_chembddb' in i[0]:
                m=i[0]
                all_dbs.append((m[:-9],))
        details=request.form
        details=details.to_dict(flat=True)
        if 'dbname' in details:
            dbname=details['dbname']+'_chembddb'
            cur.execute('use {};'.format(dbname))
            cur.execute('Select * from Property')
            properties=cur.fetchall()
            cur.execute('Select id,method_name from Model')
            results=cur.fetchall()
            cur.execute("Select * from Functional")
            functionals=cur.fetchall()
            cur.execute("Select * from Basis_set")
            basis_sets=cur.fetchall()
            cur.execute("Select * from Forcefield")
            forcefields=cur.fetchall()
            methods=[]
            for i in results:
                methods.append(i[1])
            dbname = dbname[:-9]
        if 'submit' in details:
            return render_template('delete.html',data=True,dbname=dbname,properties=properties,methods=methods,functionals=functionals,basis=basis_sets,forcefields=forcefields,all_dbs=all_dbs)
        elif 'search-query' in details:

            if 'exampleRadios' not in details:
                cur.execute('drop database {}'.format(details['dbname']))
                cur.execute('show databases;')
                all_dbs_tup=cur.fetchall()
                all_dbs=[]
                for i in all_dbs_tup:
                    if '_chembddb' in i[0]:
                        m=i[0]
                        all_dbs.append((m[:-9],))
                return render_template('delete.html',data=True,properties=properties,methods=methods,functionals=functionals,basis=basis_sets,forcefields=forcefields,all_dbs=all_dbs,success_msg='database {} deleted'.format(details['dbname']))

            elif details['exampleRadios']=='option1':
                if 'MW' in details and details['MW']!='':
                    mw_from=details['MW_from_val']
                    mw_to=details['MW_to_val']
                if 'smiles_search' in details:
                    smi = details['smiles']
                    smi_obj = pybel.readstring('smi',smi)
                    can_smi = smi_obj.write('can').strip()
                    mol_wt = round(smi_obj.molwt,3)
                    cur.execute('select id,SMILES_str,MW from Molecule where SMILES_str=\'{0}\' and (MW-{1}) < 0.00001;'.format(can_smi,mol_wt))
                    to_delete=list(cur.fetchall())
                    sql = 'delete from Value where molecule_id={};'.format(to_delete[0][0])
                    cur.execute(sql)
                    cur.execute('delete from Molecule where id={};'.format(to_delete[0][0]))
                    con.commit()
            else:
                dbname = details['dbname'] + '_chembddb'
                cur.execute('USE {};'.format(dbname))
                keys=[i for i in details if '_id' in i]
                # find molecule id if smiles_search in details
                # find MW from and to
                
                for k in keys:
                    prop_id=int(details[k][0])
                    if details[k[:-3]+'_from_val']=='' and details[k[:-3]+'_to_val']=='':
                        sql='DELETE FROM Property WHERE id={};'.format(prop_id)
                        cur.execute(sql)
                        cur.execute('use {};'.format(dbname))
                        cur.execute('Select * from Property')
                        properties=cur.fetchall()
                        cur.execute('Select id,method_name from Model')
                        results=cur.fetchall()
                        cur.execute("Select * from Functional")
                        functionals=cur.fetchall()
                        cur.execute("Select * from Basis_set")
                        basis_sets=cur.fetchall()
                        cur.execute("Select * from Forcefield")
                        forcefields=cur.fetchall()
                        methods=[]
                        for i in results:
                            methods.append(i[1])
                    else:
                        from_val=float(details[k[:-3]+'_from_val'])
                        to_val=float(details[k[:-3]+'_to_val'])
                        if from_val > to_val:
                            return render_template('delete.html',data=True, dbname=details['dbname'].replace('_chembddb',''),properties=properties,methods=methods,functionals=functionals,basis=basis_sets,forcefields=forcefields,all_dbs=all_dbs,err_msg='Minimum value for one of the properties is greater than the maximum value for it.')
                        else:
                            sql='DELETE FROM Value WHERE property_id={} and num_value > {} and num_value < {};'.format(prop_id,from_val,to_val)
                            cur.execute(sql)
                            cur.execute('select id from Molecule')
                            mol_ids = cur.fetchall()
                            cur.execute('select molecule_id from Value')
                            mol_ids_val = cur.fetchall()
                            to_delete = []
                            mol_ids_val = set(mol_ids_val)
                            for i in mol_ids:
                                if i not in mol_ids_val:
                                    to_delete.append(i[0])
                            cur.execute('delete from Molecule where id in {};'.format(str(tuple(to_delete))))
                            con.commit()
            return render_template('delete.html',data=True, dbname=details['dbname'].replace('_chembddb',''),properties=properties,methods=methods,functionals=functionals,basis=basis_sets,forcefields=forcefields,all_dbs=all_dbs,success_msg='Deleted from database {}.'.format(details['dbname'].replace('_chembddb','')))
        else:
            return render_template('delete.html',all_dbs=all_dbs)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD FOLDER'],filename)

def run_config():
    print('Open http://localhost:5000/connect')
    app.run(debug=True)
    for i in os.listdir():
        if 'chembddb' in i and 'xyz' in i:
            os.remove(i)
    # os.rmdir('./uploads')