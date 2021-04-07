import React from 'react';
import './App.css';
import logo from './logo_kinea.png'
import Modal from 'react-awesome-modal';

var Loader = require('react-loader');
// "start": "PORT=3031 react-scripts start",
// "start": "set PORT=3031 && react-scripts start",
class EditExtracted extends React.Component {
constructor(props) {
    super(props);
    this.state = {
        loaded: true,
        'data': props.data, //passed prop as initial value
        'intro': false,
        'qr': false,
        'multas': false,
        'garantia': false,
        'good':false,
        'bad':false
    }
    console.log(this.state.data)
    this.submit = {}
    this.check = {}
    this.descontos = []
    for(let i = 0; i < this.props.data.pdfContent.raw.descontos.length;i++){this.descontos.push({})}

    // this.handleInputChange = this.handleInputChange.bind(this);
    this.onSubmit = this.onSubmit.bind(this);
    this.openModal = this.openModal.bind(this);
    this.closeModal = this.closeModal.bind(this);
    }



    onSubmit(e) {
        e.preventDefault();
        this.setState({loaded:false});
        let final = {}
        for (let i in this.submit){
            if (this.check[i].checked){
                if (['tipico','proporcional','reajuste_positivo'].indexOf(this.submit[i].name) > -1){
                    if(this.submit[i].value == 'true'){ final[this.submit[i].name] = true}
                    else{ final[this.submit[i].name] = false }
                }
                else if (['andar_galpao','area','aviso_previo','data_pagamento_aluguel','data_pagamento_encargos','multa_rescisao_antecipado','periodo_carencia','vagas'].indexOf(this.submit[i].name) > -1){
                    final[this.submit[i].name] = Number(this.submit[i].value)
                }
                else{
                    final[this.submit[i].name] = this.submit[i].value
                }
                
            } 
            else{
                if (['tipico','proporcional','reajuste_positivo'].indexOf(this.submit[i].name) > -1){
                    if(this.submit[i].defaultValue == 'true'){ final[this.submit[i].name] = true}
                    else{ final[this.submit[i].name] = false }
                }
                else if (['andar_galpao','area','aviso_previo','data_pagamento_aluguel','data_pagamento_encargos','multa_rescisao_antecipado','periodo_carencia','vagas'].indexOf(this.submit[i].name) > -1){
                    final[this.submit[i].name] = Number(this.submit[i].defaultValue)
                }
                else{
                    final[this.submit[i].name] = this.submit[i].defaultValue
                }
                
            } 
        }
        final['descontos'] = []
        for (let j in this.descontos) {
            let temp = {}
            if (this.descontos[j]['checked'].checked){
                temp['data_inicio_desconto'] = this.descontos[j]['data_inicio'].value
                temp['data_final_desconto'] = this.descontos[j]['data_fim'].value
                temp['aluguel'] = this.descontos[j]['valor'].value
            }
            else{
                temp['data_inicio_desconto'] = this.descontos[j]['data_inicio'].defaultValue 
                temp['data_final_desconto'] = this.descontos[j]['data_fim'].defaultValue 
                temp['aluguel'] = this.descontos[j]['valor'].defaultValue 
            }
            final['descontos'].push(temp)
        }
        console.log(final)
        // const data = new FormData();
        // data.append('dados', JSON.stringify(final));
        fetch('http://localhost:5051/salesforce', {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: 'POST',
            body: JSON.stringify(final),
            }).then((response) => {
                // response.json().then((body) => {
                //   console.log(body)
                // });
                console.log(response.status)
                if (response.status == 500) {
                    // throw new Error("Bad response from server");
                    this.openModal('bad')
                }
                if (response.status == 200) {
                    // throw new Error("Bad response from server");
                    this.openModal('good')
                }
              });
              
    }

    // handleInputChange(event) {
    //     const target = event.target;
    //     // const value = target.type === 'checkbox' ? target.checked : target.value;
    //     const value = target.value;
    //     const name = target.name;
    
    //     // this.setState({
    //     //   [name]: value
    //     // });
    //     this.setState(final => ({
    //         ...final,
    //         [name]: value}))
    //     // console.log(this.state)
    //   }

   to_list() {
    let lista = [];
    for (var key in this.props.data.pdfContent.raw) {
        lista.push([key,this.props.data.pdfContent.raw[key],this.props.data.pdfContent.tratado[key]])
    }
    return lista
    }

    openModal(name) {
        // console.log(this.state.data.pdfContent.big_text)
        this.setState({
            [name] : true,
            loaded: true
        });
    }

    closeModal(name) {
        this.setState({
            [name] : false
        });
    }

  render() {
    //   console.log(this.props.data.pdfContent.raw)
    // let items = this.to_list()
    // let itemList=items.map((item)=>{
    //     return(
    //         <div className='card_data'>
    //              <h4 className='title'>{item[0]}</h4>
    //              <p className='subtitle'>{item[1]}</p>
    //              <input type='text' className='data_edit' defaultValue={item[2]}></input>
    //          </div>
    //     ) 
    //   })

        let itemList=this.props.data.pdfContent.tratado.descontos.map((item,index)=>{
        return(
            <div className='card_data'>
                 <h4 className='title'>Desconto</h4>
                 <p className='subtitle'>Prazo</p>
                 {(!item.data_inicio_desconto) ? <p className='subtitle'>{item.periodo[0]}</p>:''}
                 <input ref={(c) => this.descontos[index]['data_inicio'] = c} type='text' className='data_edit_big' defaultValue={item.data_inicio_desconto}></input>
                 <input ref={(c) => this.descontos[index]['data_fim'] = c} style={{marginTop: 6 + 'px'}} type='text' className='data_edit_big' defaultValue={item.data_final_desconto}></input>
                 <p className='subtitle'>Valor</p>
                 <input ref={(c) => this.descontos[index]['valor'] = c} type='text' className='data_edit' defaultValue={item.desconto}></input>
                 <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.descontos[index]['checked'] = c} />Alterado</label>       
             </div>
        ) 
      })
      
    return (
      <div className='total_grid'>
        <h1 className='title2' >Confira o Conteúdo Extraído</h1>
        <div className='data_grid'>
            <button name='intro' className='b_clausulas' onClick={() => this.openModal('intro')}>Início</button>
            <button name='qr' className='b_clausulas' onClick={() => this.openModal('qr')}>Quadro Resumo</button>
            <button name='multas' className='b_clausulas' onClick={() => this.openModal('multas')}>Multas</button>
            <button name='garantia' className='b_clausulas' onClick={() => this.openModal('garantia')}>Garantia</button>
        </div>
        <Modal visible={this.state.intro} className='modal-body'  effect="fadeInUp" onClickAway={() => this.closeModal('intro')}>
                    <div className='card_data'>
                        <h1>Início</h1>
                        <p className='content'>{this.state.data.pdfContent.big_text.intro}</p>
                        <a href="javascript:void(0);" onClick={() => this.closeModal('intro')}>Fechar</a>
                    </div>     
        </Modal>
        <Modal visible={this.state.qr} className='modal-body'   effect="fadeInUp" onClickAway={() => this.closeModal('qr')}>
                    <div className='card_data'>
                        <h1>Quadro Resumo</h1>
                        <p>{this.state.data.pdfContent.big_text.qr}</p>
                        <a href="javascript:void(0);" onClick={() => this.closeModal('qr')}>Fechar</a>
                    </div>     
        </Modal>
        <Modal visible={this.state.multas} className='modal-body' effect="fadeInUp" onClickAway={() => this.closeModal('multas')}>
                    <div className='card_data'>
                        <h1>Cláusula de Multa</h1>
                        <p>{this.state.data.pdfContent.big_text.multa}</p>
                        <a href="javascript:void(0);" onClick={() => this.closeModal('multas')}>Fechar</a>
                    </div>     
        </Modal>
        <Modal visible={this.state.garantia} className='modal-body'   effect="fadeInUp" onClickAway={() => this.closeModal('garantia')}>
                    <div className='card_data'>
                        <h1>Cláusula de Garantia</h1>
                        <p>{this.state.data.pdfContent.big_text.garantia}</p>
                        <a href="javascript:void(0);" onClick={() => this.closeModal('garantia')}>Fechar</a>
                    </div>     
        </Modal>
        <form>
        <div className='data_grid'>
            <div className='card_data'>
                <h4 className='title'>Contrato Típico</h4>
                <p className='subtitle'>{this.props.data.pdfContent.raw.tipico}</p>
                {/* onChange={this.handleInputChange}  */}
                <input name='tipico' type='text' className='data_edit' defaultValue={this.state.data.pdfContent.tratado.tipico} ref={(c) => this.submit.tipico = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.tipico = c} />Alterado</label>       
                
            </div>
            <div className='card_data'>
                <h4 className='title'>Locatária</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.locataria}</p>
                <input name = 'locataria' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.locataria} ref={(c) => this.submit.locataria = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.locataria = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Tipo do imóvel</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.tipo_imovel}</p>
                <input name = 'tipo_imovel' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.tipo_imovel} ref={(c) => this.submit.tipo_imovel = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.tipo_imovel = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Nome do Imóvel</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.nome }</p>
                <input name = 'nome' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.nome } ref={(c) => this.submit.nome = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.nome = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Área do Imóvel</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.area}</p>
                <input name = 'area' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.area} ref={(c) => this.submit.area = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.area = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                {/* <h4 className='title'>Andar ou Galpão</h4> */}
                {this.state.data.pdfContent.raw.andar ? <h4 className='title'>Andar</h4>:''}
                {this.state.data.pdfContent.raw.galpao ? <h4 className='title'>Galpão</h4>:''}
                <p className='subtitle'>{this.state.data.pdfContent.raw.andar || this.state.data.pdfContent.raw.galpao }</p>
                <input name = 'andar_galpao' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.andar ||this.state.data.pdfContent.tratado.galpao} ref={(c) => this.submit.andar_galpao = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.andar_galpao= c} />Alterado</label>       
            </div>
            <div className='card_data'>
                {/* <h4 className='title'>Pavimento/Torre ou Docas</h4> */}
                {this.state.data.pdfContent.raw.torre_docas ? <h4 className='title'>Torre ou Pavimento</h4>:''}
                {this.state.data.pdfContent.raw.docas ? <h4 className='title'>Docas</h4>:''}
                <p className='subtitle'>{this.state.data.pdfContent.raw.torre_docas  || this.state.data.pdfContent.raw.docas }</p>
                <input name = 'torre_pavimento' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.torre_docas  || this.state.data.pdfContent.tratado.docas } ref={(c) => this.submit.torre_docas = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.torre_docas = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Vagas</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.vagas }</p>
                <input name = 'vagas' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.vagas } ref={(c) => this.submit.vagas = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.vagas = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Início Vigência</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.data_inicial }</p>
                <input name = 'inicio_vigencia' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.inicio_vigencia } ref={(c) => this.submit.inicio_vigencia = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.inicio_vigencia = c} />Alterado</label>            
            </div>
            <div className='card_data'>
                <h4 className='title'>Fim Vigência</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.prazo }</p>
                <input name = 'fim_vigencia' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.fim_vigencia } ref={(c) => this.submit.fim_vigencia = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.fim_vigencia= c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Valor Aluguel</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.valor_aluguel }</p>
                <input name = 'valor_aluguel' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.valor_aluguel } ref={(c) => this.submit.valor_aluguel = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.valor_aluguel = c} />Alterado</label>                  
            </div>
            <div className='card_data'>
                <h4 className='title'>Data de Reajuste</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.data_reajuste }</p>
                <input name = 'data_reajuste' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.data_reajuste } ref={(c) => this.submit.data_reajuste= c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.data_reajuste= c} />Alterado</label>        
            </div>
            <div className='card_data'>
                <h4 className='title'>Data Início da Carência</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.data_inicio_carencia}</p>
                <input name = 'data_inicio_carencia' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.data_inicio_carencia } ref={(c) => this.submit.data_inicio_carencia = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.data_inicio_carencia = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Data do Fim da Carência</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.periodo_carencia}</p>
                <input name = 'data_fim_carencia' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.data_fim_carencia } ref={(c) => this.submit.periodo_carencia = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.periodo_carencia = c} />Alterado</label>       
            </div>
            {itemList}
            <div className='card_data'>
                <h4 className='title'>Reajuste Positivo</h4>
                {/* <p className='subtitle'>{this.props.data.pdfContent.raw.reajuste_positivo}</p> */}
                <input name = 'reajuste_positivo' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.reajuste_positivo } ref={(c) => this.submit.reajuste_positivo = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.reajuste_positivo = c} />Alterado</label>       

            </div>
            <div className='card_data'>
                <h4 className='title'>Índice do Reajuste</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.indice}</p>
                <input name = 'indice' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.indice } ref={(c) => this.submit.indice = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.indice= c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Forma de Pagamento Aluguel</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.pagamento_aluguel}</p>
                <input name = 'pagamento_aluguel' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.pagamento_aluguel } ref={(c) => this.submit.pagamento_aluguel = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.pagamento_aluguel = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Data de Pagamento do Aluguel</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.data_pagamento_aluguel}</p>
                <input name = 'data_pagamento_aluguel' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.data_pagamento_aluguel } ref={(c) => this.submit.data_pagamento_aluguel = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.data_pagamento_aluguel = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Forma de Pagamento dos Encargos</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.pagamento_encargos}</p>
                <input name = 'pagamento_encargos' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.pagamento_encargos } ref={(c) => this.submit.pagamento_encargos = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.pagamento_encargos = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Data de Pagamento Encargos</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.data_pagamento_encargos}</p>
                <input name = 'data_pagamento_encargos' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.data_pagamento_encargos } ref={(c) => this.submit.data_pagamento_encargos = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.data_pagamento_encargos = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Garantia</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.garantia}</p>
                <input name = 'garantia' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.garantia} ref={(c) => this.submit.garantia = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.garantia = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Valor da Garantia</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.valor_garantia}</p>
                <input name = 'valor_garantia' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.valor_garantia} ref={(c) => this.submit.valor_garantia = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.valor_garantia = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Aviso Prévio</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.aviso_previo}</p>
                <input name = 'aviso_previo' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.aviso_previo} ref={(c) => this.submit.aviso_previo = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.aviso_previo = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Multa por Rescisão Antecipada</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.multa_rescisao_antecipado}</p>
                <input name = 'multa_rescisao_antecipado' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.multa_rescisao_antecipado} ref={(c) => this.submit.multa_rescisao_antecipado = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.multa_rescisao_antecipado = c} />Alterado</label>        
            </div>
            <div className='card_data'>
                <h4 className='title'>Multa Proporcional</h4>
                {/* <p className='subtitle'>{this.props.data.pdfContent.raw.proporcional}</p> */}
                <input name = 'proporcional' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.proporcional} ref={(c) => this.submit.proporcional= c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.proporcional = c} />Alterado</label>          
            </div>
            <div className='card_data'>
                <h4 className='title'>Multa por Inadimplência</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.multa_inadimplencia}</p>
                <input name = 'multa_inadimplencia' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.multa_inadimplencia} ref={(c) => this.submit.multa_inadimplencia = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.multa_inadimplencia = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Prazos para Multas</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.prazos_multas}</p>
                <input name = 'prazos_multas' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.prazos_multas} ref={(c) => this.submit.prazos_multas = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.prazos_multas = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Juros ao mês</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.juros_ao_mes}</p>
                <input name = 'juros_ao_mes' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.juros_ao_mes} ref={(c) => this.submit.juros_ao_mes = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.juros_ao_mes = c} />Alterado</label>       
            </div>
            <div className='card_data'>
                <h4 className='title'>Data de Assinatura do Contrato</h4>
                <p className='subtitle'>{this.state.data.pdfContent.raw.data_assinatura}</p>
                <input name = 'data_assinatura' type='text' className='data_edit_big' defaultValue={this.state.data.pdfContent.tratado.data_assinatura} ref={(c) => this.submit.data_assinatura = c}></input>
                <label className='alterado_check'><input className='alterado_check' type='checkbox' ref={(c) => this.check.data_assinatura = c} />Alterado</label>                 
            </div>
        </div>
        </form>
        <Loader loaded={this.state.loaded} ></Loader>
        <div>
            <button className='b_extrair' onClick={this.onSubmit}>Enviar</button>     
        </div>
        <Modal visible={this.state.good} className='modal-body'  effect="fadeInUp" onClickAway={() => this.closeModal('good')}>
                    <div className='card_data'>
                        <h1>Contrato cadastrado com sucesso!</h1>
                        <p className='content'>Recarregue a página para realizar um novo cadastro</p>
                        <a href="javascript:void(0);" onClick={() => this.closeModal('good')}>Fechar</a>
                    </div>     
        </Modal>
        <Modal visible={this.state.bad} className='modal-body'  effect="fadeInUp" onClickAway={() => this.closeModal('bad')}>
                    <div className='card_data'>
                        <h1>Erro no cadastro</h1> 
                        <p className='content'>Isso pode acontecer pelas seguintes razões:</p>
                        <ul>
                            <li>Algum dado não está formatado da maneira correta</li>
                            <li>Pode ter algum dado faltante</li>
                            <li>Sua conexão pode estar instável</li>

                        </ul>
                        <a href="javascript:void(0);" onClick={() => this.closeModal('bad')}>Fechar</a>
                    </div>     
        </Modal>
      </div>
    );
  }
}

export default EditExtracted;