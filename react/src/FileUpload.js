import React from 'react';
import './App.css';
import logo from './logo_kinea.png'

import EditExtracted from './EditExtracted';

var Loader = require('react-loader');

class FileUpload extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      pdfContent: '',
      loaded: false,
      content: false

    };
    this.handleUploadPDF = this.handleUploadPDF.bind(this);
  }

  componentDidMount() {
    this.setState.loaded=false;
  }

  handleUploadPDF(ev) {
    ev.preventDefault();
    const data = new FormData();
    data.append('file', this.uploadInput.files[0]);
    data.append('entrega_de_chaves', this.entrega_de_chaves.value)
    this.setState({loaded:true});
    fetch('http://localhost:5051/upload', {
      method: 'POST',
      body: data,
    }).then((response) => {
      response.json().then((body) => {
        this.setState({ pdfContent: body});
        // console.log(this.state.pdfContent)
      });
      this.setState({loaded:false, content: true});
    });
  }

  render() {
    return (
      <div>
        <div className='Box'>
          <div ><h2 className='title'>Leitor de Contratos</h2><img src={logo} alt="Logo" /></div>
          <h1 className='title'>Upload do Contrato</h1>
          
        <form onSubmit={this.handleUploadPDF} >
          <div>
            <input ref={(ref) => { this.entrega_de_chaves= ref; }} name = 'data_entrega_de_chaves' type='text' className='data_edit_entregachaves'  placeholder='Insira aqui a data(dd/mm/aaaa) do Termo de Entrega de Chaves se houver.'></input>
            {/* <p className='text_entregachaves'>Insira a data do Termo de Entrega de Chaves se houver</p> */}
            <p className='subtitle'>Faça o upload do contrato para extrair seus dados</p>
            <input className='b_selecionar' ref={(ref) => { this.uploadInput = ref; }} type="file" />
          </div>
          <br />
          <div>
            <button className='b_extrair'>Extrair</button>     
          </div>
        </form>
        <Loader loaded={!this.state.loaded} ></Loader>
        </div>
        {(this.state.content && this.state.pdfContent) ? <div className='conteudo'><EditExtracted data={this.state}/></div>:''}
      </div>
    );
  }
}

export default FileUpload;