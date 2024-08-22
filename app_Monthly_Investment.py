import streamlit as st
import plotly.graph_objects as go
import numpy as np


def app_Monthly_Investment():
    def format_number(number):
        """문자열을 3자리마다 콤마로 구분된 문자열로 변환"""
        try:
            return f"{int(number):,}"
        except ValueError:
            return number

    # 타이틀과 서브헤더
    st.title("투자 시뮬레이션")

    # 입력 폼
    with st.form(key='investment_form'):
        initial_capital = st.text_input("초기 자본금 (KRW)", value=format_number("10000000"))
        initial_capital_hold_period = st.number_input("초기 자본금 보유 기간 (개월)", value=0)
        monthly_saving = st.text_input("월 저축액 (KRW)", value=format_number("1000000"))
        monthly_saving_period = st.number_input("월 저축 기간 (개월)", value=120)
        annual_return_rate = st.number_input("연간 수익률 (%)", value=10.00)
        total_investment_period_months = st.number_input("총 투자 기간 (개월)", value=240)
        target_asset = st.text_input("목표 자산 금액 (KRW)", value=format_number("100000000"))

        # 제출 버튼
        submit_button = st.form_submit_button(label="시뮬레이션 실행")

    # 경고 메시지
    warning_message = st.empty()

    if submit_button:
        try:
            initial_capital = float(initial_capital.replace(',', ''))
            monthly_saving = float(monthly_saving.replace(',', ''))
            target_asset = float(target_asset.replace(',', ''))
            
            if initial_capital_hold_period + monthly_saving_period > total_investment_period_months:
                warning_message.warning("초기 자본금 보유 기간과 월 저축 기간의 합이 총 투자 기간을 초과합니다.")
            else:
                # 자산 계산
                asset = initial_capital
                total_investment = initial_capital
                monthly_return_rate = (1 + annual_return_rate / 100) ** (1 / 12) - 1
                asset_list = [asset]
                investment_list = [initial_capital]
                profit_list = [0]
                target_reached_month = None

                for month in range(1, total_investment_period_months + 1):
                    if initial_capital_hold_period < month <= initial_capital_hold_period + monthly_saving_period:
                        asset = asset * (1 + monthly_return_rate) + monthly_saving
                        total_investment += monthly_saving
                    else:
                        asset = asset * (1 + monthly_return_rate)
                    asset_list.append(asset)
                    investment_list.append(total_investment)
                    profit_list.append(asset - total_investment)
                    
                    if asset >= target_asset and target_reached_month is None:
                        target_reached_month = month

                months = np.arange(0, total_investment_period_months + 1)

                # 목표 도달 시점 표시
                if target_reached_month is not None:
                    st.success(f"목표 자산 금액에 {target_reached_month}개월 후 도달했습니다!")
                else:
                    st.warning("목표 자산 금액에 도달하지 못했습니다.")

                # 비주얼 대시보드 생성
                fig = go.Figure()

                # 총 저축액
                fig.add_trace(go.Bar(
                    x=months, y=investment_list, name='총 저축액',
                    marker_color='rgba(0, 123, 255, 0.6)',
                    hovertemplate='<b>개월:</b> %{x}<br>'
                                '<b>총 투자액:</b> %{y:,.0f} KRW<br>'
                                '<b>이익:</b> %{text:,.0f} KRW<br>'
                                '<b>총 자산:</b> %{customdata:,.0f} KRW<extra></extra>',
                    text=profit_list,  # 이익 정보
                    customdata=asset_list  # 총 자산 정보
                ))

                # 이익
                fig.add_trace(go.Bar(
                    x=months, y=profit_list, name='이익',
                    marker_color='rgba(40, 167, 69, 0.6)',
                    hovertemplate='<b>개월:</b> %{x}<br>'
                                '<b>총 투자액:</b> %{customdata:,.0f} KRW<br>'
                                '<b>이익:</b> %{y:,.0f} KRW<br>'
                                '<b>총 자산:</b> %{text:,.0f} KRW<extra></extra>',
                    customdata=investment_list,  # 총 투자액 정보
                    text=asset_list  # 총 자산 정보
                ))

                # 총 자산
                fig.add_trace(go.Scatter(
                    x=months, y=asset_list, name='총 자산',
                    mode='lines+markers',
                    marker=dict(color='rgba(255, 99, 132, 0.8)', size=6),
                    line=dict(color='rgba(255, 99, 132, 1)', width=2),
                    hovertemplate='<b>개월:</b> %{x}<br>'
                                '<b>총 투자액:</b> %{customdata:,.0f} KRW<br>'
                                '<b>이익:</b> %{text:,.0f} KRW<br>'
                                '<b>총 자산:</b> %{y:,.0f} KRW<extra></extra>',
                    customdata=investment_list,  # 총 투자액 정보
                    text=profit_list  # 이익 정보
                ))

                fig.update_layout(
                    title='월별 저축 투자 결과',
                    barmode='group',
                    xaxis_title='개월',
                    yaxis_title='금액 (KRW)',
                    yaxis_tickformat=',d',
                    hovermode='closest',
                    plot_bgcolor='rgba(0,0,0,0)',  # 배경을 투명하게 설정
                    paper_bgcolor='rgba(0,0,0,0)',  # 종이 배경을 투명하게 설정
                    hoverlabel=dict(bgcolor='white', font_size=12),
                    annotations=[{
                        'x': months[-1],
                        'y': asset_list[-1],
                        'xref': 'x',
                        'yref': 'y',
                        'text': f"최종 자산: {int(asset_list[-1]):,} KRW",
                        'showarrow': True,
                        'arrowhead': 7,
                        'ax': -100,
                        'ay': 0,
                        'font': {'color': 'black', 'size': 12},
                        'arrowcolor': 'black'
                    }]
                )

                st.plotly_chart(fig)

        except ValueError:
            st.error("모든 필드에 유효한 숫자를 입력해 주세요.")