    <form  action=/user >
        <input type=number name=id />
        <input type=file name=pic_file />
        <input type=text name=name nullable=false unique=true />
        <input type=email name=email unique=true nullable=false />
        <input type=uuid name=secret_token nullable=true />
        <input type=password name=secret_password nullable=false />
    </form>
    <br/>
    <form action=/comment >
        <input type="datetime-local" name=created_at_time default="func.now()" />
        <input type=number name=id />
        <input type=number name=user_id reference=user.id nullable=false />
        <input type=number name=comment_id reference=comment.id ondelete=cascade >
        <textarea name=message rows=10 cols=50 nullable=false ></textarea>
        <input type=url name=factoid />
        <%include file="category.mako" args='category="category"'  />
    </form>
    <br/>
    <form action=/transition >
        <input type=number name=id />
        <input type=number name=previous_comment_id reference=comment.id nullable=false />
        <input type=number name=next_comment_id reference=comment.id nullable=false />
    </form>
   <br/>
    <form action=/annexe >
        <input type=number name=id nullable=false reference=comment.id ondelete=cascade >
        <input type=file name=annexe_file nullable=false />
    </form>
   <br/>
    <form action=/text >
        <input type=number name=id />
        <input type=number name=user_id reference=user.id nullable=false />
        <input type=number name=comment_id reference=comment.id ondelete=cascade >
        <input type=number name=book_order default=200 >
        <textarea name=text rows=100 cols=80 nullable=false ></textarea>
   </form>
   <br/>




