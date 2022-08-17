
class Form extends React.Component{

    constructor(props){
        super(props)
        this.state = {
            matrix: [],
            base_elements: [],
            composition: [],
            specification: []
        }   
    }

    async componentDidMount(){
        const base_elements = await fetch('/api/base_element').then(result => result.json())
    }

    render(){
        return(
            <section>
                <div>
                    <button onClick={() => addMatrix()}>
                        <i>+</i>
                        <span>Add Matrix</span>   
                    </button>
                </div>
                <section>
                    <div>
                    {
                        this.state.matrix.map(item => {
                            return <Matrix datas={item}/>
                        })
                    }
                </div>
                </section>
            </section>
        )
    }
}

function Matrix({datas}){
    return(
        <section>
        </section>
    )
}

ReactDOM.render(<Form/>, document.getElementById('form'))