/*
 * copyright (c) 2013 Nathan Skipper, Montgomery Technology, Inc.
 *
 * This file is part of ObjectiveMedia (http://nskipper1110.github.com/objectivemedia).
 *
 * ObjectiveMedia is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * ObjectiveMedia is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with ObjectiveMedia; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */
package objectivemediasample;
import com.mti.primitives.Primitives;
/**
 *
 * @author nathan
 */
public class ObjectiveMediaSample {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        try {
            for (javax.swing.UIManager.LookAndFeelInfo info : javax.swing.UIManager.getInstalledLookAndFeels()) {
                if ("Nimbus".equals(info.getName())) {
                    javax.swing.UIManager.setLookAndFeel(info.getClassName());
                    break;
                }
            }
        } catch (ClassNotFoundException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (InstantiationException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (IllegalAccessException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (javax.swing.UnsupportedLookAndFeelException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        }
        //</editor-fold>

        /* Create and display the form */
        java.awt.EventQueue.invokeLater(new Runnable() {
            public void run() {
                String separator = System.getProperty("file.separator");
                String binpath = System.getProperty("java.home");
                String archtype = System.getProperty("os.arch");
                String osname = System.getProperty("os.name");
                String osversion = System.getProperty("os.version");
                String userhome = System.getProperty("user.home");
                if(osname.toLowerCase().contains("linux")){
                    if(archtype.contains("amd64")){
                        Primitives.LibraryPath = userhome + "/objectivemedia/linux/ObjectiveMedia/dist/Debug64/lin64/";
                        Primitives.NativeLibraries.add("ObjectiveMedia_lin64.so");
                        
                    }
                    else{
                        Primitives.LibraryPath = userhome + "/objectivemedia/linux/objectivemedia/dist/debug/lin32/";
                        Primitives.NativeLibraries.add("libobjectivemedia.so");
                    }
                }
                else if(osname.toLowerCase().contains("win")){
                    if(archtype.contains("amd64")){
                        Primitives.LibraryPath = "C:\\objectivemedia\\build\\debug\\win64\\";
                        Primitives.NativeLibraries.add("objectivemedia_win64.dll");
                    }
                    else{
                        Primitives.LibraryPath = "C:\\objectivemedia\\build\\debug\\win32\\";
                        Primitives.NativeLibraries.add("objectivemedia_win32.dll");
                    }
                }
                Primitives.InitializePrimitives();
                MainForm fm = new MainForm();
                fm.setSize(680, 600);
                fm.setVisible(true);
                fm.setTitle("ObjectiveMedia Sample App");
            }
        });
    }
}
