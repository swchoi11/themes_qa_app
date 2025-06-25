import streamlit as st
import pandas as pd
import os
from PIL import Image
import json
from typing import Dict, Any
import tempfile

class ExcelReviewApp:
    def __init__(self):
        self.df = None
        self.filtered_df = None
        self.modified_df = None  # 수정된 행들만 저장할 데이터프레임
        self.modified_indices = set()  # 수정된 행의 인덱스를 추적
        self.current_index = 0
        self.total_records = 0
        self.image_directory = ""
        self.selected_assignee = None
        
    def load_excel_file(self, uploaded_file):
        """xlsx 파일 로드"""
        try:
            self.df = pd.read_excel(uploaded_file)
            
            # gt 성공/실패와 reason 성공/실패 컬럼을 문자열 타입으로 변환
            if 'gt 성공/실패' in self.df.columns:
                self.df['gt 성공/실패'] = self.df['gt 성공/실패'].astype(str)
                self.df['gt 성공/실패'] = self.df['gt 성공/실패'].replace('nan', '')
            
            if 'reason 성공/실패' in self.df.columns:
                self.df['reason 성공/실패'] = self.df['reason 성공/실패'].astype(str)
                self.df['reason 성공/실패'] = self.df['reason 성공/실패'].replace('nan', '')
            
            # 수정된 데이터프레임을 빈 데이터프레임으로 초기화 (원본과 같은 컬럼 구조)
            self.modified_df = pd.DataFrame(columns=self.df.columns)
            self.modified_indices = set()
            
            # filtered_df는 필터링이 적용될 때까지 초기화하지 않음
            if self.filtered_df is None:
                self.filtered_df = self.df.copy()  # 초기에는 전체 데이터
            
            self.total_records = len(self.df)
            st.success(f"Excel 파일 로드 완료: {self.total_records}개 레코드")
            return True
        except Exception as e:
            st.error(f"Excel 파일 로드 실패: {e}")
            return False
    
    def set_image_directory(self, directory_path):
        """이미지 디렉토리 설정"""
        if os.path.exists(directory_path):
            self.image_directory = directory_path
            st.success(f"이미지 디렉토리 설정 완료: {directory_path}")
            return True
        else:
            st.error(f"디렉토리를 찾을 수 없습니다: {directory_path}")
            return False
    
    def filter_by_assignee(self, assignee):
        """담당자별 필터링"""
        if self.df is None:
            return False
        
        if assignee == "전체":
            self.filtered_df = self.df.copy()
        else:
            # 필터링
            self.filtered_df = self.df[self.df['담당자'] == assignee].copy()
        
        # 인덱스를 0부터 시작하도록 리셋
        self.filtered_df.reset_index(drop=True, inplace=True)
        
        self.total_records = len(self.filtered_df)
        self.current_index = 0
        self.selected_assignee = assignee
        
        return True
    
    def get_assignees(self):
        """담당자 목록 반환"""
        if self.df is None:
            return []
        return ["전체"] + sorted(self.df['담당자'].unique().tolist())
    
    def get_current_record(self):
        """현재 레코드 반환"""
        if self.filtered_df is None or self.current_index >= self.total_records:
            return None
        
        return self.filtered_df.iloc[self.current_index]
    
    def find_image_file(self, image_name):
        """이미지 파일 찾기"""
        if not self.image_directory:
            return None
            
        # 이미지명에서 확장자 제거 (이미 확장자가 포함된 경우)
        base_name = os.path.splitext(image_name)[0]
        
        # 다양한 확장자로 시도
        extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        for ext in extensions:
            image_path = os.path.join(self.image_directory, base_name + ext)
            if os.path.exists(image_path):
                return image_path
                
        # 파일명에 확장자가 포함된 경우
        image_path = os.path.join(self.image_directory, image_name)
        if os.path.exists(image_path):
            return image_path
            
        # 디버깅을 위한 로그
        st.write(f"이미지를 찾을 수 없습니다. 검색한 경로들:")
        for ext in extensions:
            st.write(f"  - {os.path.join(self.image_directory, base_name + ext)}")
        st.write(f"  - {os.path.join(self.image_directory, image_name)}")
            
        return None
    
    def display_current_record(self):
        """현재 레코드 표시"""
        if self.filtered_df is None:
            st.warning("먼저 엑셀 파일을 업로드해주세요.")
            return
        
        if self.current_index >= self.total_records:
            st.success("모든 레코드 검수가 완료되었습니다!")
            return
        
        record = self.get_current_record()
        if record is None:
            return
        
        # 진행률 표시
        progress = (self.current_index + 1) / self.total_records
        st.progress(progress)
        st.write(f"진행률: {self.current_index + 1} / {self.total_records}")
        
        # 현재 담당자 정보 표시
        if hasattr(self, 'selected_assignee') and self.selected_assignee:
            st.write(f"**담당자: {self.selected_assignee}**")
        
        # 이미지명 표시
        image_name = record.get('FileName', '')
        st.subheader(f"이미지명: {image_name}")
        
        # 좌우 분할 레이아웃
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📷 이미지")
            # 이미지 표시
            image_path = self.find_image_file(image_name)
            if image_path:
                try:
                    # 파일이 실제로 파일인지 확인
                    if os.path.isfile(image_path):
                        image = Image.open(image_path)
                        st.image(image, caption=image_name)
                    else:
                        st.error(f"경로가 파일이 아닙니다: {image_path}")
                except Exception as e:
                    st.error(f"이미지 로드 실패: {e}")
                    st.write(f"시도한 경로: {image_path}")
            else:
                st.warning(f"이미지를 찾을 수 없습니다: {image_name}")
        
        with col2:
            st.subheader("📊 레코드 정보")
            # 평가 결과 표시
            self.display_evaluation_results(record)
            
            # 검수 입력 폼
            st.subheader("✏️ 검수 결과 입력")
            self.display_review_form(record)
    
    def display_evaluation_results(self, record):
        """평가 결과 표시"""
        # 수정 불가능한 컬럼들 (읽기 전용)
        read_only_columns = ['no', '담당자', 'FileName', 'GroundTruth', 'Predict', 'MATCH', 'Score', 'ItemName', 'Location', 'Desc']
        
        # reason 열을 먼저 강조 표시
        if 'Reason' in record.index:
            reason_value = record['Reason']
            if pd.notna(reason_value):
                st.markdown("**🔍 Reason (중요):**")
                st.info(f"{reason_value}")
                st.markdown("---")
        
        # 나머지 읽기 전용 컬럼들 표시
        st.markdown("**📋 기타 정보 (읽기 전용):**")
        for col in record.index:
            if col in read_only_columns and col != 'Reason':
                value = record[col]
                if pd.notna(value):  # NaN이 아닌 경우만 표시
                    st.write(f"**{col}**: {value}")
        
        # 수정 가능한 컬럼들 표시
        editable_columns = ['gt 성공/실패', 'reason 성공/실패']
        st.markdown("**✏️ 수정 가능한 항목:**")
        for col in editable_columns:
            if col in record.index:
                value = record[col]
                if pd.notna(value):
                    st.write(f"**{col}**: {value}")
                else:
                    st.write(f"**{col}**: (비어있음)")
    
    def display_review_form(self, record):
        """검수 입력 폼 표시"""
        with st.form("review_form"):
            # 수정 가능한 컬럼들만 입력받기
            editable_columns = ['gt 성공/실패', 'reason 성공/실패']
            updated_values = {}
            
            for col in editable_columns:
                if col in record.index:
                    current_value = record[col]
                    if pd.isna(current_value):
                        current_value = ""
                    
                    # 컬럼 타입에 따라 다른 입력 방식 사용
                    if isinstance(current_value, (int, float)):
                        new_value = st.number_input(
                            f"{col} 수정",
                            value=float(current_value) if current_value != "" else 0.0,
                            key=f"input_{col}_{self.current_index}"
                        )
                    elif isinstance(current_value, bool):
                        new_value = st.checkbox(
                            f"{col} 수정",
                            value=current_value,
                            key=f"input_{col}_{self.current_index}"
                        )
                    else:
                        # 성공/실패 선택을 위한 드롭다운
                        options = ["성공", "실패", ""]
                        current_option = str(current_value) if current_value != "" else ""
                        if current_option not in options:
                            current_option = ""
                        
                        new_value = st.selectbox(
                            f"{col} 수정",
                            options=options,
                            index=options.index(current_option),
                            key=f"input_{col}_{self.current_index}"
                        )
                    
                    updated_values[col] = new_value
            
            # 버튼들
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.form_submit_button("⬅️ 이전"):
                    if self.current_index > 0:
                        self.current_index -= 1
                        st.rerun()
            
            with col2:
                if st.form_submit_button("💾 저장"):
                    self.save_current_record(updated_values)
                    st.success("저장되었습니다!")
            
            with col3:
                if st.form_submit_button("다음 ➡️"):
                    # 자동 저장
                    self.save_current_record(updated_values)
                    if self.current_index < self.total_records - 1:
                        self.current_index += 1
                        st.rerun()
    
    def save_current_record(self, updated_values):
        """현재 레코드 저장"""
        if self.filtered_df is not None:
            # 필터링된 데이터에서 현재 레코드 가져오기
            current_record = self.filtered_df.iloc[self.current_index]
            
            # 원본 데이터에서 해당 레코드의 인덱스 찾기
            # FileName을 기준으로 매칭
            file_name = current_record.get('FileName', '')
            original_index = self.df[self.df['FileName'] == file_name].index[0]
            
            # 수정사항이 있는지 확인
            has_changes = False
            for col, value in updated_values.items():
                current_value = self.df.at[original_index, col]
                if str(current_value) != str(value):
                    has_changes = True
                    break
            
            if has_changes:
                # 수정된 행을 modified_df에 추가
                modified_row = self.df.iloc[original_index].copy()
                
                for col, value in updated_values.items():
                    try:
                        # gt 성공/실패와 reason 성공/실패는 항상 문자열로 처리
                        if col in ['gt 성공/실패', 'reason 성공/실패']:
                            value = str(value) if value is not None else ''
                        else:
                            # 다른 컬럼들은 원본 데이터 타입에 맞게 변환
                            original_dtype = self.df[col].dtype
                            
                            if pd.api.types.is_bool_dtype(original_dtype):
                                # bool 타입인 경우
                                if isinstance(value, str):
                                    if value.lower() in ['true', '1', 'yes']:
                                        value = True
                                    elif value.lower() in ['false', '0', 'no', '']:
                                        value = False
                                    else:
                                        value = bool(value)
                                else:
                                    value = bool(value)
                            elif pd.api.types.is_integer_dtype(original_dtype):
                                # int 타입인 경우
                                if value == '' or pd.isna(value):
                                    value = 0
                                else:
                                    value = int(float(value))
                            elif pd.api.types.is_float_dtype(original_dtype):
                                # float 타입인 경우
                                if value == '' or pd.isna(value):
                                    value = 0.0
                                else:
                                    value = float(value)
                            else:
                                # 문자열 타입인 경우
                                value = str(value) if value is not None else ''
                        
                        modified_row[col] = value
                        
                    except (ValueError, TypeError) as e:
                        st.error(f"컬럼 '{col}'의 값 '{value}'를 저장할 수 없습니다: {e}")
                        return
                
                # 세션 상태에서 modified_df와 modified_indices 가져오기
                modified_df = st.session_state.get('modified_df', None)
                modified_indices = st.session_state.get('modified_indices', set())
                
                # 이미 수정된 행인지 확인
                if original_index in modified_indices:
                    # 기존 수정된 행을 업데이트
                    if modified_df is not None and len(modified_df) > 0:
                        existing_idx = modified_df[modified_df.index == original_index].index
                        if len(existing_idx) > 0:
                            modified_df.loc[existing_idx[0]] = modified_row
                else:
                    # 새로운 수정된 행 추가
                    # concat 경고 해결을 위해 더 안전한 방식 사용
                    if modified_df is None or len(modified_df) == 0:
                        # 첫 번째 행인 경우
                        modified_df = pd.DataFrame([modified_row])
                    else:
                        # 기존 데이터가 있는 경우
                        new_df = pd.DataFrame([modified_row])
                        modified_df = pd.concat([modified_df, new_df], ignore_index=False)
                    
                    modified_indices.add(original_index)
                
                # 세션 상태에 저장
                st.session_state.modified_df = modified_df
                st.session_state.modified_indices = modified_indices
                
                st.success(f"수정사항이 저장되었습니다. (총 {len(modified_df)}개 행 수정됨)")
            else:
                st.info("수정사항이 없습니다.")
    
    def save_excel_file(self, output_path):
        """수정된 엑셀 파일 저장"""
        modified_df = st.session_state.get('modified_df', None)
        modified_indices = st.session_state.get('modified_indices', set())
        
        if modified_df is not None and len(modified_df) > 0:
            # 인덱스를 리셋하여 깔끔하게 저장
            modified_df.reset_index(drop=True, inplace=True)
            modified_df.to_excel(output_path, index=False)
            st.success(f"수정된 {len(modified_df)}개 행이 저장되었습니다: {output_path}")
            return True
        else:
            st.warning("저장할 수정된 데이터가 없습니다.")
            return False

def main():
    st.set_page_config(
        page_title="이미지 평가 결과 검수 시스템",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 이미지 평가 결과 검수 시스템")
    
    # 세션 상태 초기화
    if 'app' not in st.session_state:
        st.session_state.app = ExcelReviewApp()
    
    if 'modified_df' not in st.session_state:
        st.session_state.modified_df = None
    
    if 'modified_indices' not in st.session_state:
        st.session_state.modified_indices = set()
    
    app = st.session_state.app
    
    # 사이드바 설정
    with st.sidebar:
        st.header("설정")
        
        # 엑셀 파일 업로드
        st.subheader("1. xlsx 파일 업로드")
        uploaded_file = st.file_uploader(
            "평가 결과가 담긴 xlsx 파일을 선택하세요",
            type=['xlsx']
        )
        
        if uploaded_file is not None:
            if app.load_excel_file(uploaded_file):
                st.session_state.excel_loaded = True
        
        # 담당자 선택
        if hasattr(st.session_state, 'excel_loaded') and st.session_state.excel_loaded:
            st.subheader("담당자 선택")
            assignees = app.get_assignees()
            if assignees:
                # 현재 선택된 담당자 표시
                if hasattr(app, 'selected_assignee') and app.selected_assignee:
                    st.write(f"현재 선택된 담당자: **{app.selected_assignee}**")
                
                selected_assignee = st.selectbox(
                    "검수할 담당자를 선택하세요",
                    options=assignees,
                    index=0
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("담당자 필터 적용"):
                        if app.filter_by_assignee(selected_assignee):
                            st.success(f"담당자 '{selected_assignee}' 필터 적용 완료: {app.total_records}개 레코드")
                            st.session_state.assignee_filtered = True
                
                with col2:
                    if st.button("필터 초기화"):
                        st.session_state.assignee_filtered = False
        
        # 이미지 디렉토리 설정
        st.subheader("2. 이미지 디렉토리 설정")
        image_dir = st.text_input(
            "이미지가 저장된 디렉토리 경로를 입력하세요",
            placeholder="예: /home/user/Downloads/images"
        )
        
        if st.button("디렉토리 설정"):
            if app.set_image_directory(image_dir):
                st.session_state.image_dir_set = True
        
        # 검수 진행률
        if hasattr(app, 'df') and app.df is not None:
            st.subheader("검수 진행률")
            progress = (app.current_index + 1) / app.total_records if app.total_records > 0 else 0
            st.progress(progress)
            st.write(f"{app.current_index + 1} / {app.total_records}")
            
            # 수정된 행 개수 표시
            modified_count = 0
            modified_df = st.session_state.get('modified_df', None)
            modified_indices = st.session_state.get('modified_indices', set())
            
            if modified_df is not None:
                modified_count = len(modified_df)
            st.write(f"📝 수정된 행: {modified_count}개")
        
        # 파일 저장
        st.subheader("3. 파일 저장")
        if st.button("수정된 엑셀 파일 저장"):
            if app.df is not None:
                output_path = "검수완료_" + uploaded_file.name if uploaded_file else "검수완료_result.xlsx"
                app.save_excel_file(output_path)
    
    # 메인 화면
    if hasattr(st.session_state, 'excel_loaded') and st.session_state.excel_loaded:
        if hasattr(st.session_state, 'image_dir_set') and st.session_state.image_dir_set:
            if hasattr(st.session_state, 'assignee_filtered') and st.session_state.assignee_filtered:
                app.display_current_record()
            else:
                st.info("사이드바에서 담당자를 선택하고 필터를 적용해주세요.")
        else:
            st.warning("이미지 디렉토리를 설정해주세요.")
    else:
        st.info("사이드바에서 엑셀 파일을 업로드하고 이미지 디렉토리를 설정해주세요.")

if __name__ == "__main__":
    main() 