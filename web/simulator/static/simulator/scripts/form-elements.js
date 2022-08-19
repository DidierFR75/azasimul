
class Form extends React.Component{

    constructor(props){
        super(props)
        this.state = {
            forms: {},
            models: {}
        }
    }

    componentDidMount(){
        let forms = {}, models = {}
        const types = ['base_element', 'base_element_value', 'specification', 'possible_specification', 'composition']
        Promise.all(types.map(element => {
            return new Promise(async(resolve) => {
                const model = await fetch('/api/base_element', {
                    method: 'OPTIONS'
                }).then(response => response.json())
                models[element] = model.actions.POST
                forms[element] =  await fetch(`/api/${element}`).then(response => response.json())
                if(models[element] && forms[element]) resolve()
            })
        })).then(() => {
            console.log(forms, models)
            this.setState({
                forms: { forms },
                models: { models }
            }, () => {
                console.log(this.state)
            })
        })
        // types.map(async(element) => {
        //     const model = await fetch('/api/base_element', {
        //         method: 'OPTIONS'
        //     }).then(response => response.json())
        //     models[element] = model.actions.POST
        //     forms[element] =  await fetch(`/api/${element}`).then(response => response.json())
        // })
        console.log(this.state.forms, this.state.models)
        
        
        
    }

    render(){
        return(
            this.state.forms && this.state.models ?
            (
                <section className="form-elements-wrp">
                    <Elements type='base_element' forms={this.state.forms['base_element']} model={this.state.models['base_element']}/>
                    <Elements type='possible_specification' forms={this.state.forms.possible_specification} model={this.state.models.possible_specification} />
                    <Elements type='composition' forms={this.state.forms.base_element_value} model={this.state.models.base_element_value}>
                        <Elements type='specification' forms={this.state.forms.specification} model={this.state.models.specification} />
                    </Elements>
                </section>
            ) : <div></div>
        )
    }
}

function Elements({ type, forms, model, count, children }){


    React.useEffect(() => {
        console.log('reload', forms, model)
    }, [forms, count])

    return(
        <ul>
            <section className="button-wrp">
                <button>Add { type.replaceAll('_', ' ') }</button>
            </section>
            {
                forms && forms.map(form => {
                    return(
                        <li key={form.id}>
                            <Element model={model} form={form} />
                        </li>
                    )
                })
            }
            { children }
        </ul>
    )
}

function Element({ model, form }){
    
    const types = {
        'field': 'text',
        'string': 'text',
        'float': 'number'
    }

    const renderField = (key, field, value) => {
        return(
            <div class="field-wrp">
                <label>{ field.label }</label>
                { renderInput(key, field, value) }
            </div>
        )
    }

    const renderInput = (key, field, value) => {
        if(model[key].type === 'choice'){
            return(
                <select name={key}>
                    {
                        model[key].choices.map(option => {
                            return <option value={option.value}>{option.display_name}</option>
                        })
                    }
                </select>
            )
        }
        return(
            <input name={key} type={types[field.type]} required={field.required} value={value} />
        )
    }

    return(
        <section className="form-wrp">
        {
            model && [...model].map(key => {
                if(!model[key].read_only) return renderField(key, model[key], form && form[key] || null)
            })
        }
        </section>
    )
}

ReactDOM.render(<Form/>, document.getElementById('form'))