var vm = new Vue({
    el: '#app',

	// 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host: host,
        order_submitting: false, // 正在提交订单标志
        pay_method: 2, // 支付方式,默认支付宝支付
        nowsite: '', // 默认地址
        payment_amount: '',


    },
    mounted(){
        // 初始化
        this.payment_amount = payment_amount;
        // 绑定默认地址
        this.nowsite = default_address_id;
    },
    methods: {
        // 提交订单
        on_order_submit(){
            if (!this.nowsite) {
                alert('请补充收货地址');
                return;
            }
            if (!this.pay_method) {
                alert('请选择付款方式');
                return;
            }
            if (this.order_submitting == false){
                this.order_submitting = true;
                var url = this.host + '/orders/commit/';
                axios.post(url, {
                        address_id: this.nowsite,
                        pay_method: this.pay_method
                    }, {
                        headers:{
                            'X-CSRFToken':getCookie('csrftoken')
                        },
                        responseType: 'json'
                    })
                    .then(response => {
                        if (response.data.code == '0') {
                            location.href = '/orders/success/?order_id='+response.data.order_id
                                        +'&payment_amount='+this.payment_amount
                                        +'&pay_method='+this.pay_method;
                            // 倒计时60秒，60秒后允许用户再次点击发送短信验证码的按钮
                        // var num = 60;
                        // // 设置一个计时器
                        // var t = setInterval(() => {
                        //     if (num == 1) {
                        //         // 如果计时器到最后, 清除计时器对象
                        //         clearInterval(t);
                        //         // 将点击获取验证码的按钮展示的文本回复成原始文本
                        //         this.sms_code_tip = '支付时间已过期';
                        //         // 将点击按钮的onclick事件函数恢复回去
                        //         // this.sending_flag = false;
                        //     } else {
                        //         num -= 1;
                        //         // 展示倒计时信息
                        //         this.sms_code_tip = num + '秒';
                        //     }
                        // }, 1000, 60);
                        } else if (response.data.code == '4101') {
                            location.href = '/login/?next=/orders/settlement/';
                        } else {
                            alert(response.data.errmsg);
                        }
                    })
                    .catch(error => {
                        this.order_submitting = false;
                        console.log(error.response);
                    })
            }
        }
    }
});
